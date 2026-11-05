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

    attendance = member.attendance_records.order_by("-attendance_date")[:6]
    room_assignments = member.room_assignments.select_related("room").order_by("-effective_from")[:4]
    area_assignments = member.area_assignments.select_related("area").order_by("-effective_from")[:4]
    context = {
        "member": member,
        "attendance": attendance,
        "attendance_count": member.attendance_records.count(),
        "room_assignments": room_assignments,
        "area_assignments": area_assignments,
    }
    return render(request, "dashboard/index.html", context)
