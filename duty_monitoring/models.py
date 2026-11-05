from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from assignments.models import AreaAssignment, RoomAssignment
from members.models import SAPMember


class RoomCleaningRecord(models.Model):
    class Phase(models.TextChoices):
        BEFORE_CLASS = "before_class", "Before class"
        AFTER_CLASS = "after_class", "After class"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        NOT_REQUIRED = "not_required", "Not required"

    room_assignment = models.ForeignKey(
        RoomAssignment,
        on_delete=models.PROTECT,
        related_name="cleaning_records",
    )
    duty_date = models.DateField()
    phase = models.CharField(max_length=20, choices=Phase.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        SAPMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_room_cleanings",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-duty_date", "room_assignment", "phase"]
        constraints = [
            models.UniqueConstraint(
                fields=["room_assignment", "duty_date", "phase"],
                name="unique_room_cleaning_phase_per_day",
            )
        ]

    def clean(self):
        if self.status == self.Status.COMPLETED and not self.completed_at:
            raise ValidationError("Completed cleaning records must have a completion time.")

    def __str__(self):
        return f"{self.room_assignment} — {self.duty_date} — {self.get_phase_display()}"


class AreaDutySession(models.Model):
    area_assignment = models.ForeignKey(
        AreaAssignment,
        on_delete=models.PROTECT,
        related_name="duty_sessions",
    )
    member = models.ForeignKey(
        SAPMember,
        on_delete=models.CASCADE,
        related_name="area_duty_sessions",
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_area_duty_sessions",
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["member", "started_at"]),
        ]

    def clean(self):
        if self.ended_at and self.ended_at <= self.started_at:
            raise ValidationError("The session end must be later than its start.")

        if self.area_assignment_id and self.member_id:
            if self.area_assignment.member_id != self.member_id:
                raise ValidationError(
                    "The session member must match the area assignment member."
                )

    @property
    def duration_minutes(self):
        if not self.ended_at:
            return 0
        seconds = (self.ended_at - self.started_at).total_seconds()
        return int(seconds // 60)

    def __str__(self):
        return f"{self.member} — {self.started_at:%Y-%m-%d %H:%M}"
