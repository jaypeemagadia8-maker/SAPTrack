from django.contrib import admin

from .models import AreaDutySession, RoomCleaningRecord


@admin.register(RoomCleaningRecord)
class RoomCleaningRecordAdmin(admin.ModelAdmin):
    list_display = ("room_assignment", "duty_date", "phase", "status", "completed_at")
    list_filter = ("duty_date", "phase", "status")


@admin.register(AreaDutySession)
class AreaDutySessionAdmin(admin.ModelAdmin):
    list_display = ("member", "area_assignment", "started_at", "ended_at")
    list_filter = ("started_at",)
    search_fields = ("member__student_number", "member__user__username")
