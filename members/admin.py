from django.contrib import admin

from .models import SAPMember


@admin.register(SAPMember)
class SAPMemberAdmin(admin.ModelAdmin):
    list_display = ("student_number", "user", "is_active", "date_joined")
    list_filter = ("is_active", "date_joined")
    search_fields = ("student_number", "user__username", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
