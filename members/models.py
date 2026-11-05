from django.conf import settings
from django.db import models


class SAPMember(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sap_member",
    )
    student_number = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["student_number"]

    def __str__(self):
        full_name = self.user.get_full_name()
        return f"{self.student_number} — {full_name or self.user.username}"
