from django.core.exceptions import ValidationError
from django.db import models

from members.models import SAPMember


class AttendanceRecord(models.Model):
    member = models.ForeignKey(
        SAPMember,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    attendance_date = models.DateField()
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_attendance",
    )

    class Meta:
        ordering = ["-attendance_date", "member"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "attendance_date"],
                name="unique_member_attendance_per_day",
            )
        ]

    def clean(self):
        if self.time_out and self.time_out <= self.time_in:
            raise ValidationError("Time-out must be later than time-in.")

    def __str__(self):
        return f"{self.member} — {self.attendance_date}"
