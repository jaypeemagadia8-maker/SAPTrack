from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import SAPMember


class StudentLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Student number or username",
        widget=forms.TextInput(
            attrs={"autofocus": True, "autocomplete": "username", "placeholder": "e.g. 2026-00123"}
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "placeholder": "Enter your password"}
        ),
    )

    def clean(self):
        entered_username = self.cleaned_data.get("username")
        if entered_username:
            member = SAPMember.objects.select_related("user").filter(student_number=entered_username).first()
            if member:
                self.data = self.data.copy()
                self.data[self.username_field] = member.user.get_username()

        data = super().clean()
        user = self.get_user()
        if user is not None:
            member = SAPMember.objects.filter(user=user).first()
            if member is None or not member.is_active:
                raise ValidationError(
                    "This is not an active student account. Please contact your SAP coordinator."
                )
        return data
