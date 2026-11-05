from django.shortcuts import render

from members.models import SAPMember


def index(request):
    members = SAPMember.objects.select_related("user").all()
    context = {
        "title": "SAPTrack Dashboard",
        "members": members,
    }
    return render(request, "dashboard/index.html", context)
