from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .forms import StudentLoginForm


class StudentLoginView(auth_views.LoginView):
    template_name = "members/login.html"
    authentication_form = StudentLoginForm
    redirect_authenticated_user = True
    next_page = reverse_lazy("dashboard_index")


class StudentLogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("members:login")


class StudentPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "members/password_change.html"
    success_url = reverse_lazy("dashboard_index")
