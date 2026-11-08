from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="dashboard_index"),
    path("coordinator/", views.coordinator_dashboard, name="coordinator_dashboard"),
    path("coordinator/tasks/<int:task_id>/review/", views.review_task, name="review_task"),
    path("reports.csv", views.report_csv, name="report_csv"),
    path("attendance/time-in/", views.time_in, name="time_in"),
    path("duty/start/", views.start_duty, name="start_duty"),
    path("duty/end/", views.end_duty, name="end_duty"),
    path("tasks/<int:task_id>/submit/", views.submit_task, name="submit_task"),
    path("", include("members.urls")),
]
