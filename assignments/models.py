from django.core.exceptions import ValidationError
from django.db import models

from members.models import SAPMember


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RoomAssignment(models.Model):
    member = models.ForeignKey(
        SAPMember,
        on_delete=models.CASCADE,
        related_name="room_assignments",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["member", "room", "effective_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "room", "effective_from"],
                name="unique_member_room_assignment_start",
            )
        ]

    def clean(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("The end date must be on or after the start date.")

    def __str__(self):
        return f"{self.member} — {self.room}"


class AreaAssignment(models.Model):
    member = models.ForeignKey(
        SAPMember,
        on_delete=models.CASCADE,
        related_name="area_assignments",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["member", "area", "effective_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "area", "effective_from"],
                name="unique_member_area_assignment_start",
            )
        ]

    def clean(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("The end date must be on or after the start date.")

    def __str__(self):
        return f"{self.member} — {self.area}"
