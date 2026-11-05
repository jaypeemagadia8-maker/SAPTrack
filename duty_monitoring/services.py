from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import AreaDutySession


def get_weekly_area_duty_summary(member, week_start=None):
    if week_start is None:
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())

    week_end = week_start + timedelta(days=7)
    required_minutes = getattr(settings, "SAP_WEEKLY_AREA_DUTY_REQUIRED_MINUTES", 180)

    sessions = AreaDutySession.objects.filter(
        member=member,
        started_at__date__gte=week_start,
        started_at__date__lt=week_end,
        ended_at__isnull=False,
    )

    completed_minutes = sum(session.duration_minutes for session in sessions)

    return {
        "week_start": week_start,
        "week_end": week_end - timedelta(days=1),
        "completed_minutes": completed_minutes,
        "required_minutes": required_minutes,
        "remaining_minutes": max(0, required_minutes - completed_minutes),
        "is_complete": completed_minutes >= required_minutes,
    }
