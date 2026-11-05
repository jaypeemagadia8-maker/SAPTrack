from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="dashboard_index"),
    path("", include("members.urls")),
]
