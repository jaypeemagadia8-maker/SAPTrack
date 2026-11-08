from django.contrib import admin

from .models import StudentTask


@admin.register(StudentTask)
class StudentTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "member", "due_date", "status", "submitted_at", "verified_at")
    list_filter = ("status", "due_date")
    search_fields = ("title", "member__student_number", "member__user__username")
    readonly_fields = ("created_at", "submitted_at", "verified_at")
