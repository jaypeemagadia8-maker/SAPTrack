# SAPTrack student sign-in

The student sign-in page is available at `/login/` and the student portal at `/` (when `dashboard.urls` is included at the project root). Student accounts are provisioned by staff in Django admin: create a Django User, then create a SAPMember linked to that user and enter the student's number. Students sign in with their Django username and password. Only active SAPMember accounts can access the portal.

If the project-level URL configuration does not already include the dashboard routes, add `path("", include("dashboard.urls"))` to `config/urls.py`. Student sign-out is a POST action and is protected by Django CSRF middleware.
