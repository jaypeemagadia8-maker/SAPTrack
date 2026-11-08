import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from attendance.models import AttendanceRecord
from assignments.models import AreaAssignment
from duty_monitoring.models import AreaDutySession
from duty_monitoring.services import get_weekly_area_duty_summary
from members.models import SAPMember

from .models import StudentTask


def _get_active_member(request):
    try:
        member = request.user.sap_member
    except SAPMember.DoesNotExist:
        return None
    return member if member.is_active else None


@login_required
def index(request):
    member = _get_active_member(request)
    if member is None:
        if request.user.is_staff:
            return redirect("coordinator_dashboard")
        messages.error(request, "Your student account is inactive or not linked. Please contact your SAP coordinator.")
        return redirect("members:login")

    today = timezone.localdate()
    today_attendance = member.attendance_records.filter(attendance_date=today).first()
    open_duty = member.area_duty_sessions.filter(ended_at__isnull=True).select_related(
        "area_assignment__area"
    ).first()
    current_area_assignment = AreaAssignment.objects.filter(
        member=member,
        effective_from__lte=today,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today)).select_related(
        "area"
    ).order_by("-effective_from").first()
    attendance = member.attendance_records.order_by("-attendance_date")[:8]
    room_assignments = member.room_assignments.select_related("room").order_by("-effective_from")[:5]
    area_assignments = member.area_assignments.select_related("area").order_by("-effective_from")[:5]
    area_sessions = member.area_duty_sessions.select_related("area_assignment__area").order_by("-started_at")[:5]
    duty_progress = get_weekly_area_duty_summary(member)
    tasks = member.tasks.all()
    due_tasks = tasks.exclude(status=StudentTask.Status.VERIFIED).filter(
        due_date__isnull=False, due_date__gte=today
    ).order_by("due_date")[:3]
    overdue_tasks = tasks.exclude(status=StudentTask.Status.VERIFIED).filter(
        due_date__lt=today
    ).order_by("due_date")[:3]
    context = {
        "member": member,
        "attendance": attendance,
        "today_attendance": today_attendance,
        "open_duty": open_duty,
        "current_area_assignment": current_area_assignment,
        "attendance_count": member.attendance_records.count(),
        "attendance_this_month": member.attendance_records.filter(
            attendance_date__year=today.year, attendance_date__month=today.month
        ).count(),
        "room_assignments": room_assignments,
        "area_assignments": area_assignments,
        "area_sessions": area_sessions,
        "duty_progress": duty_progress,
        "tasks": tasks[:8],
        "due_tasks": due_tasks,
        "overdue_tasks": overdue_tasks,
    }
    return render(request, "dashboard/index.html", context)


@login_required
@require_POST
def time_in(request):
    member = _get_active_member(request)
    if member is None:
        messages.error(request, "Your account is inactive. Please contact your SAP coordinator.")
        return redirect("members:login")
    today = timezone.localdate()
    record, created = AttendanceRecord.objects.get_or_create(
        member=member,
        attendance_date=today,
        defaults={"time_in": timezone.now(), "recorded_by": request.user},
    )
    if created:
        messages.success(request, "Attendance submitted. Your time-in has been recorded.")
    elif record.time_out:
        messages.info(request, "Your attendance for today is already complete.")
    else:
        messages.info(request, "Your time-in was already recorded today.")
    return redirect("dashboard_index")


@login_required
@require_POST
def start_duty(request):
    member = _get_active_member(request)
    if member is None:
        messages.error(request, "Your account is inactive. Please contact your SAP coordinator.")
        return redirect("members:login")

    today = timezone.localdate()
    if not member.attendance_records.filter(attendance_date=today).exists():
        messages.error(request, "Submit your attendance before starting duty.")
        return redirect("dashboard_index")

    with transaction.atomic():
        # Locking the member serializes concurrent start requests on databases that support row locks.
        locked_member = SAPMember.objects.select_for_update().get(pk=member.pk)
        if locked_member.area_duty_sessions.filter(ended_at__isnull=True).exists():
            messages.info(request, "You already have an active duty session. End it before starting another.")
            return redirect("dashboard_index")
        assignment = AreaAssignment.objects.filter(
            member=locked_member,
            effective_from__lte=today,
        ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today)).select_related(
            "area"
        ).order_by("-effective_from").first()
        if assignment is None:
            messages.error(request, "You do not have an active area assignment for today. Please contact your coordinator.")
            return redirect("dashboard_index")
        AreaDutySession.objects.create(
            member=locked_member,
            area_assignment=assignment,
            started_at=timezone.now(),
            recorded_by=request.user,
        )
    messages.success(request, f"Duty started at {assignment.area.name}. Use End Duty when you finish.")
    return redirect("dashboard_index")


@login_required
@require_POST
def end_duty(request):
    member = _get_active_member(request)
    if member is None:
        messages.error(request, "Your account is inactive. Please contact your SAP coordinator.")
        return redirect("members:login")
    with transaction.atomic():
        session = member.area_duty_sessions.select_for_update().filter(
            ended_at__isnull=True
        ).order_by("-started_at").first()
        if session is None:
            messages.error(request, "There is no active duty session to end.")
        else:
            session.ended_at = timezone.now()
            session.save(update_fields=["ended_at"])
            messages.success(request, "Duty ended and recorded. You are still logged in to SAPTrack.")
    return redirect("dashboard_index")


@login_required
@require_POST
def submit_task(request, task_id):
    member = _get_active_member(request)
    if member is None:
        messages.error(request, "Your account is inactive. Please contact your SAP coordinator.")
        return redirect("members:login")
    task = get_object_or_404(StudentTask, pk=task_id, member=member)
    if task.status == StudentTask.Status.TODO:
        task.mark_submitted()
        messages.success(request, "Your task was submitted for coordinator review.")
    else:
        messages.info(request, "This task has already been submitted or verified.")
    return redirect("dashboard_index")


def _is_coordinator(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_coordinator)
def coordinator_dashboard(request):
    query = request.GET.get("q", "").strip()
    members = SAPMember.objects.select_related("user").order_by("student_number")
    if query:
        members = members.filter(
            Q(student_number__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
        )
    pending_tasks = StudentTask.objects.filter(
        status=StudentTask.Status.SUBMITTED
    ).select_related("member__user").order_by("submitted_at", "due_date")
    context = {
        "query": query,
        "members": members[:100],
        "student_count": SAPMember.objects.count(),
        "pending_tasks": pending_tasks,
        "pending_task_count": pending_tasks.count(),
        "today": timezone.localdate(),
    }
    return render(request, "dashboard/coordinator.html", context)


@user_passes_test(_is_coordinator)
@require_POST
def review_task(request, task_id):
    task = get_object_or_404(
        StudentTask.objects.select_related("member"),
        pk=task_id,
        status=StudentTask.Status.SUBMITTED,
    )
    action = request.POST.get("action")
    if action == "verify":
        task.status = StudentTask.Status.VERIFIED
        task.verified_at = timezone.now()
        task.verified_by = request.user
        task.save(update_fields=["status", "verified_at", "verified_by"])
        messages.success(request, f"The task '{task.title}' has been verified as complete.")
    elif action == "return":
        task.status = StudentTask.Status.TODO
        task.submitted_at = None
        task.save(update_fields=["status", "submitted_at"])
        messages.info(request, f"The task '{task.title}' was returned to the student for revision.")
    else:
        return HttpResponseBadRequest("Unknown review action.")
    return redirect("coordinator_dashboard")


@user_passes_test(_is_coordinator)
def report_csv(request):
    start_text = request.GET.get("start", "").strip()
    end_text = request.GET.get("end", "").strip()
    start = parse_date(start_text) if start_text else None
    end = parse_date(end_text) if end_text else None
    if (start_text and start is None) or (end_text and end is None):
        return HttpResponseBadRequest("Enter valid dates in YYYY-MM-DD format.")
    if start and end and start > end:
        return HttpResponseBadRequest("The start date must be on or before the end date.")

    report_type = request.GET.get("type", "attendance")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response.write("\ufeff")
    writer = csv.writer(response)
    if report_type == "duty":
        response["Content-Disposition"] = 'attachment; filename="saptrack-duty-report.csv"'
        writer.writerow(["Student number", "Student", "Area", "Started at", "Ended at", "Minutes"])
        records = AreaDutySession.objects.select_related(
            "member__user", "area_assignment__area"
        ).filter(ended_at__isnull=False)
        if start:
            records = records.filter(started_at__date__gte=start)
        if end:
            records = records.filter(started_at__date__lte=end)
        for record in records.order_by("started_at"):
            writer.writerow([
                record.member.student_number,
                record.member.user.get_full_name() or record.member.user.username,
                record.area_assignment.area.name,
                timezone.localtime(record.started_at).isoformat(),
                timezone.localtime(record.ended_at).isoformat(),
                record.duration_minutes,
            ])
    elif report_type == "attendance":
        response["Content-Disposition"] = 'attachment; filename="saptrack-attendance-report.csv"'
        writer.writerow(["Student number", "Student", "Date", "Time in", "Time out", "Notes"])
        records = AttendanceRecord.objects.select_related("member__user").all()
        if start:
            records = records.filter(attendance_date__gte=start)
        if end:
            records = records.filter(attendance_date__lte=end)
        for record in records.order_by("attendance_date", "member__student_number"):
            writer.writerow([
                record.member.student_number,
                record.member.user.get_full_name() or record.member.user.username,
                record.attendance_date.isoformat(),
                timezone.localtime(record.time_in).isoformat() if record.time_in else "",
                timezone.localtime(record.time_out).isoformat() if record.time_out else "",
                record.notes,
            ])
    else:
        return HttpResponseBadRequest("Unknown report type.")
    return response
