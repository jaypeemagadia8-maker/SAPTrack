import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from attendance.models import AttendanceRecord
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
        messages.error(request, "Hindi aktibo o hindi naka-link ang student account mo. Makipag-ugnayan sa SAP coordinator.")
        return redirect("members:login")

    today = timezone.localdate()
    attendance = member.attendance_records.order_by("-attendance_date")[:8]
    room_assignments = member.room_assignments.select_related("room").order_by("-effective_from")[:5]
    area_assignments = member.area_assignments.select_related("area").order_by("-effective_from")[:5]
    area_sessions = member.area_duty_sessions.select_related("area_assignment__area").order_by("-started_at")[:5]
    duty_progress = get_weekly_area_duty_summary(member)
    tasks = member.tasks.all()
    due_tasks = tasks.exclude(status=StudentTask.Status.VERIFIED).filter(due_date__isnull=False, due_date__gte=today).order_by("due_date")[:3]
    overdue_tasks = tasks.exclude(status=StudentTask.Status.VERIFIED).filter(due_date__lt=today).order_by("due_date")[:3]
    attendance_this_month = member.attendance_records.filter(
        attendance_date__year=today.year, attendance_date__month=today.month
    ).count()
    context = {
        "member": member,
        "attendance": attendance,
        "attendance_count": member.attendance_records.count(),
        "attendance_this_month": attendance_this_month,
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
def submit_task(request, task_id):
    member = _get_active_member(request)
    if member is None:
        messages.error(request, "Hindi aktibo ang account mo. Makipag-ugnayan sa SAP coordinator.")
        return redirect("members:login")
    if request.method != "POST":
        return redirect("dashboard_index")
    task = get_object_or_404(StudentTask, pk=task_id, member=member)
    task.mark_submitted()
    messages.success(request, "Naipasa ang task mo para ma-review ng coordinator.")
    return redirect("dashboard_index")


def _is_coordinator(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_coordinator)
def coordinator_dashboard(request):
    query = request.GET.get("q", "").strip()
    members = SAPMember.objects.select_related("user").order_by("student_number")
    if query:
        from django.db.models import Q
        members = members.filter(
            Q(student_number__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
        )
    context = {
        "query": query,
        "members": members[:100],
        "student_count": SAPMember.objects.count(),
        "pending_tasks": StudentTask.objects.filter(status=StudentTask.Status.SUBMITTED).count(),
        "today": timezone.localdate(),
    }
    return render(request, "dashboard/coordinator.html", context)


@user_passes_test(_is_coordinator)
def report_csv(request):
    start_text = request.GET.get("start", "").strip()
    end_text = request.GET.get("end", "").strip()
    start = parse_date(start_text) if start_text else None
    end = parse_date(end_text) if end_text else None
    if (start_text and start is None) or (end_text and end is None):
        return HttpResponseBadRequest("Gumamit ng valid na petsa sa YYYY-MM-DD format.")
    if start and end and start > end:
        return HttpResponseBadRequest("Dapat mas maaga o kapareho ng end date ang start date.")

    report_type = request.GET.get("type", "attendance")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response.write("\ufeff")
    writer = csv.writer(response)
    if report_type == "duty":
        response["Content-Disposition"] = 'attachment; filename="saptrack-duty-report.csv"'
        writer.writerow(["Student number", "Student", "Area", "Started at", "Ended at", "Minutes"])
        records = AreaDutySession.objects.select_related("member__user", "area_assignment__area").filter(ended_at__isnull=False)
        if start:
            records = records.filter(started_at__date__gte=start)
        if end:
            records = records.filter(started_at__date__lte=end)
        for record in records.order_by("started_at"):
            writer.writerow([record.member.student_number, record.member.user.get_full_name() or record.member.user.username, record.area_assignment.area.name, timezone.localtime(record.started_at).isoformat(), timezone.localtime(record.ended_at).isoformat(), record.duration_minutes])
    elif report_type == "attendance":
        response["Content-Disposition"] = 'attachment; filename="saptrack-attendance-report.csv"'
        writer.writerow(["Student number", "Student", "Date", "Time in", "Time out", "Notes"])
        records = AttendanceRecord.objects.select_related("member__user").all()
        if start:
            records = records.filter(attendance_date__gte=start)
        if end:
            records = records.filter(attendance_date__lte=end)
        for record in records.order_by("attendance_date", "member__student_number"):
            writer.writerow([record.member.student_number, record.member.user.get_full_name() or record.member.user.username, record.attendance_date.isoformat(), timezone.localtime(record.time_in).isoformat() if record.time_in else "", timezone.localtime(record.time_out).isoformat() if record.time_out else "", record.notes])
    else:
        return HttpResponseBadRequest("Hindi kilalang report type.")
    return response
