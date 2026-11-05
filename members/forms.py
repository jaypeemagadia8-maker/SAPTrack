from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


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
        data = super().clean()
        user = self.get_user()
        if user is not None:
            try:
                member = user.sap_member
            except user.__class__.sap_member.RelatedObjectDoesNotExist:
                member = None
            if member is None or not member.is_active:
                raise ValidationError("This account is not an active student account. Please contact your SAP coordinator.")
        return data
