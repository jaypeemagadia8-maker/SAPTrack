from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assignments.models import Area, AreaAssignment
from attendance.models import AttendanceRecord
from duty_monitoring.models import AreaDutySession
from members.models import SAPMember


class StudentAttendanceAndDutyFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="student1", password="safe-test-password")
        self.member = SAPMember.objects.create(user=self.user, student_number="2026-001")
        self.area = Area.objects.create(name="Library")
        self.assignment = AreaAssignment.objects.create(
            member=self.member,
            area=self.area,
            effective_from=timezone.localdate() - timedelta(days=1),
        )
        self.client.force_login(self.user)

    def test_dashboard_renders_reminder_and_attendance_button(self):
        response = self.client.get(reverse("dashboard_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit attendance / Time in")
        self.assertContains(response, "Your SAPTrack teacher")

    def test_time_in_is_recorded_once_per_day(self):
        url = reverse("time_in")
        first = self.client.post(url)
        second = self.client.post(url)
        self.assertRedirects(first, reverse("dashboard_index"))
        self.assertRedirects(second, reverse("dashboard_index"))
        self.assertEqual(AttendanceRecord.objects.filter(member=self.member, attendance_date=timezone.localdate()).count(), 1)

    def test_duty_cannot_start_before_attendance(self):
        response = self.client.post(reverse("start_duty"))
        self.assertRedirects(response, reverse("dashboard_index"))
        self.assertFalse(AreaDutySession.objects.filter(member=self.member).exists())

    def test_duty_can_start_and_end_without_logging_out(self):
        self.client.post(reverse("time_in"))
        start_response = self.client.post(reverse("start_duty"))
        self.assertRedirects(start_response, reverse("dashboard_index"))
        session = AreaDutySession.objects.get(member=self.member, ended_at__isnull=True)

        end_response = self.client.post(reverse("end_duty"))
        self.assertRedirects(end_response, reverse("dashboard_index"))
        session.refresh_from_db()
        self.assertIsNotNone(session.ended_at)
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_start_duty_requires_active_area_assignment(self):
        self.client.post(reverse("time_in"))
        self.assignment.delete()
        response = self.client.post(reverse("start_duty"))
        self.assertRedirects(response, reverse("dashboard_index"))
        self.assertFalse(AreaDutySession.objects.filter(member=self.member).exists())

    def test_get_request_cannot_change_attendance_or_duty(self):
        self.client.post(reverse("time_in"))
        self.assertEqual(self.client.get(reverse("start_duty")).status_code, 405)
        self.assertEqual(self.client.get(reverse("end_duty")).status_code, 405)
