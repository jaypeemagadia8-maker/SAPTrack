# SAPTrack

SAPTrack is a Django-based Student Assistance Program portal for managing student accounts, attendance, room/area assignments, and duty monitoring. The student portal uses a responsive green-and-cream interface; coordinators manage records through Django admin.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py makemigrations members assignments attendance duty_monitoring
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the student portal or `http://127.0.0.1:8000/admin/` for coordinator administration. Student sign-in is at `http://127.0.0.1:8000/login/`.

## Create student accounts

There is intentionally no public self-registration. A coordinator creates the Django User and sets a temporary password in admin, then creates a SAPMember linked to that user and enters the unique student number. Give the student their username (or student number) and temporary password through a private channel; ask them to change their password after first sign-in. Only active SAPMember accounts can use the student portal. Do not share the coordinator's superuser credentials.

## Records available

- Student profile and student number
- Attendance records
- Room and area assignments
- Area duty sessions and room-cleaning records

Students can see only records related to their own SAPMember account. Coordinators can create and update records in `/admin/`.

## Configuration and deployment

The default SQLite database and secret key are for local development only. Before deployment, set `DJANGO_SECRET_KEY` to a long random secret, set `DJANGO_DEBUG=0`, configure `DJANGO_ALLOWED_HOSTS` to the real hostnames, use a production database, run `python manage.py collectstatic`, and deploy behind HTTPS with a production WSGI/ASGI server. Do not expose Django's development server to the public internet.
