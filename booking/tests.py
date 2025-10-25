from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from users.models import Coach, Member, User
from .models import Booking


class BookingModelTests(TestCase):
    def setUp(self):
        self.user_coach = User.objects.create_user(username="coach1", password="123")
        self.user_member = User.objects.create_user(username="member1", password="123")
        self.coach = Coach.objects.create(user=self.user_coach)
        self.member = Member.objects.create(user=self.user_member)

    def test_booking_str_representation(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=timezone.localdate(),
            start_time=datetime.now().time(),
            end_time=(datetime.now() + timedelta(hours=1)).time(),
            location="Jakarta",
        )
        self.assertIn(self.member.user.username, str(booking))
        self.assertIn(self.coach.user.username, str(booking))

    def test_booking_conflict_detection(self):
        date = timezone.localdate()
        start = datetime.now().time()
        end = (datetime.now() + timedelta(hours=1)).time()
        Booking.objects.create(
            coach=self.coach, member=self.member, date=date, start_time=start, end_time=end
        )
        self.assertTrue(Booking.is_conflict(self.coach, date, start, end))

    def test_reschedule_updates_date_and_status(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=timezone.localdate() + timedelta(days=1),
            start_time=datetime.now().time(),
            end_time=(datetime.now() + timedelta(hours=1)).time(),
            status="confirmed",
        )
        new_date = timezone.localdate() + timedelta(days=2)
        new_start = (datetime.now() + timedelta(hours=2)).time()
        new_end = (datetime.now() + timedelta(hours=3)).time()

        booking.reschedule(new_date, new_start, new_end)
        booking.refresh_from_db()
        self.assertEqual(booking.date, new_date)
        self.assertEqual(booking.status, "rescheduled")

    def test_reschedule_raises_for_past_date(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=timezone.localdate(),
            start_time=datetime.now().time(),
            end_time=(datetime.now() + timedelta(hours=1)).time(),
        )
        past_date = timezone.localdate() - timedelta(days=1)
        with self.assertRaises(ValueError):
            booking.reschedule(past_date, datetime.now().time(), (datetime.now() + timedelta(hours=1)).time())


class BookingViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_coach = User.objects.create_user(username="coach1", password="123")
        self.user_member = User.objects.create_user(username="member1", password="123")
        self.coach = Coach.objects.create(user=self.user_coach)
        self.member = Member.objects.create(user=self.user_member)
        self.date = timezone.now() + timedelta(days=1)

    # ---------- Basic page views ----------
    def test_booking_list_for_member(self):
        self.client.login(username="member1", password="123")
        Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
        )
        url = reverse("booking:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MY BOOKINGS")

    def test_booking_list_for_coach(self):
        self.client.login(username="coach1", password="123")
        Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
        )
        url = reverse("booking:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BOOKING REQUESTS")

    # ---------- Create booking ----------
    def test_create_booking_requires_login(self):
        url = reverse("booking:create", args=[self.coach.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_member_can_create_booking(self):
        self.client.login(username="member1", password="123")
        url = reverse("booking:create", args=[self.coach.id])
        date_str = self.date.strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(url, {"location": "Jakarta", "date": date_str})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)

    def test_create_booking_with_invalid_date(self):
        self.client.login(username="member1", password="123")
        url = reverse("booking:create", args=[self.coach.id])
        response = self.client.post(url, {"location": "Jakarta", "date": "invalid-date"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid date/time format")

    # ---------- Edit booking ----------
    def test_edit_booking_by_member(self):
        self.client.login(username="member1", password="123")
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
        )
        url = reverse("booking:edit", args=[booking.id])
        new_time = (self.date + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(url, {"location": "Bandung", "date": new_time})
        booking.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(booking.location, "Bandung")

    # ---------- Cancel (page) ----------
    def test_cancel_booking_page(self):
        self.client.login(username="member1", password="123")
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
        )
        url = reverse("booking:cancel", args=[booking.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, "cancelled")

    # ---------- AJAX endpoints ----------
    def test_ajax_cancel_booking(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
        )
        url = reverse("booking:ajax_cancel", args=[booking.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, "cancelled")

    def test_ajax_reschedule_booking(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
        )
        url = reverse("booking:ajax_reschedule", args=[booking.id])
        new_dt = (self.date + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        body = json.dumps({"date": new_dt})
        response = self.client.post(url, body, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, "rescheduled")

    def test_ajax_reschedule_with_invalid_json(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
        )
        url = reverse("booking:ajax_reschedule", args=[booking.id])
        response = self.client.post(url, "not-json", content_type="application/json")
        self.assertIn(response.status_code, [400, 500])

    def test_ajax_accept_reschedule(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
            status="rescheduled",
        )
        url = reverse("booking:ajax_accept_reschedule", args=[booking.id])
        response = self.client.post(url)
        booking.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(booking.status, "confirmed")

    def test_ajax_reject_reschedule(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
            status="rescheduled",
        )
        url = reverse("booking:ajax_reject_reschedule", args=[booking.id])
        response = self.client.post(url)
        booking.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(booking.status, "cancelled")

    def test_ajax_confirm_booking(self):
        booking = Booking.objects.create(
            coach=self.coach,
            member=self.member,
            date=self.date.date(),
            start_time=self.date.time(),
            end_time=(self.date + timedelta(hours=1)).time(),
            status="pending",
        )
        url = reverse("booking:ajax_confirm_booking", args=[booking.id])
        response = self.client.post(url)
        booking.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(booking.status, "confirmed")
