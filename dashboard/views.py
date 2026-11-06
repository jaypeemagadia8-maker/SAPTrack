from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from members.models import SAPMember


@login_required
def index(request):
    try:
        member = request.user.sap_member
    except SAPMember.DoesNotExist:
        if request.user.is_staff:
            return redirect("admin:index")
        return redirect("members:login")

    if not member.is_active:
        return redirect("members:login")

    attendance = member.attendance_records.select_related("member").order_by("-attendance_date")[:8]
    room_assignments = member.room_assignments.select_related("room").order_by("-effective_from")[:5]
    area_assignments = member.area_assignments.select_related("area").order_by("-effective_from")[:5]
    area_sessions = member.area_duty_sessions.select_related("area_assignment__area").order_by("-started_at")[:5]
    context = {
        "member": member,
        "attendance": attendance,
        "attendance_count": member.attendance_records.count(),
        "room_assignments": room_assignments,
        "room_assignment_count": member.room_assignments.count(),
        "area_assignments": area_assignments,
        "area_assignment_count": member.area_assignments.count(),
        "area_sessions": area_sessions,
    }
    return render(request, "dashboard/index.html", context)
