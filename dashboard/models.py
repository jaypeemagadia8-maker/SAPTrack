from django.conf import settings
from django.db import models
from django.utils import timezone

from members.models import SAPMember


class StudentTask(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To do"
        SUBMITTED = "submitted", "Submitted for review"
        VERIFIED = "verified", "Verified complete"

    member = models.ForeignKey(
        SAPMember,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_student_tasks",
    )

    class Meta:
        ordering = ["status", "due_date", "title"]

    def mark_submitted(self):
        if self.status == self.Status.TODO:
            self.status = self.Status.SUBMITTED
            self.submitted_at = timezone.now()
            self.save(update_fields=["status", "submitted_at"])

    def __str__(self):
        return f"{self.member} — {self.title}"
