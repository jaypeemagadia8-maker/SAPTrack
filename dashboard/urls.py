from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="dashboard_index"),
    path("coordinator/", views.coordinator_dashboard, name="coordinator_dashboard"),
    path("coordinator/tasks/<int:task_id>/review/", views.review_task, name="review_task"),
    path("reports.csv", views.report_csv, name="report_csv"),
    path("tasks/<int:task_id>/submit/", views.submit_task, name="submit_task"),
    path("", include("members.urls")),
]
