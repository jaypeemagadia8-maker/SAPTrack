from django.urls import path

from .views import StudentLoginView, StudentLogoutView

app_name = "members"

urlpatterns = [
    path("login/", StudentLoginView.as_view(), name="login"),
    path("logout/", StudentLogoutView.as_view(), name="logout"),
]
