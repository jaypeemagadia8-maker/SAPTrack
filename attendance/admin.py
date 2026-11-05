from django.contrib import admin

from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("member", "attendance_date", "time_in", "time_out")
    list_filter = ("attendance_date",)
    search_fields = ("member__student_number", "member__user__username")
