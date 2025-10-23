from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from users.models import Coach, Member
from booking.models import Booking


class BookingModelTest(TestCase):
    def setUp(self):
        self.coach = Coach.objects.create(name="Coach A")
        self.member = Member.objects.create(name="Member A")
        self.future_date = timezone.now().date() + timedelta(days=3)
        self.booking = Booking.objects.create(date=self.future_date)
        self.booking.coach.add(self.coach)
        self.booking.member.add(self.member)

    def test_create_booking(self):
        """Pastikan booking baru berhasil dibuat"""
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(self.booking.status, "pending")
        self.assertEqual(self.booking.coach.first().name, "Coach A")

    def test_conflict_detection(self):
        """Tidak boleh ada dua booking dengan coach dan tanggal sama"""
        conflict_date = self.future_date
        conflict_booking = Booking(date=conflict_date)
        conflict_booking.save()
        conflict_booking.coach.add(self.coach)

        # harus True karena bentrok
        self.assertTrue(Booking.is_conflict(self.coach, conflict_date))

    def test_reschedule_success(self):
        """Pastikan reschedule berhasil ke tanggal depan"""
        new_date = timezone.now().date() + timedelta(days=10)
        self.booking.reschedule(new_date)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.date, new_date)
        self.assertEqual(self.booking.status, "rescheduled")

    def test_reschedule_to_past_fails(self):
        """Tidak boleh reschedule ke waktu yang sudah lewat"""
        past_date = timezone.now().date() - timedelta(days=3)
        with self.assertRaises(ValueError):
            self.booking.reschedule(past_date)

    def test_cancel_booking(self):
        """Pastikan cancel booking ubah status jadi cancelled"""
        self.booking.status = 'cancelled'
        self.booking.save()
        self.assertEqual(self.booking.status, 'cancelled')


class BookingViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.coach = Coach.objects.create(name="Coach A")
        self.member = Member.objects.create(name="Member A")
        self.booking = Booking.objects.create(date=timezone.now().date() + timedelta(days=5))
        self.booking.coach.add(self.coach)
        self.booking.member.add(self.member)

    def test_booking_list_view(self):
        """Cek apakah halaman list tampil"""
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coach A")

    def test_create_booking_view(self):
        """Cek apakah bisa buat booking lewat POST"""
        future_date = timezone.now().date() + timedelta(days=7)
        response = self.client.post(reverse('create_booking'), {
            'coaches': [self.coach.id],
            'members': [self.member.id],
            'date': future_date
        })
        self.assertEqual(response.status_code, 302)  # redirect
        self.assertEqual(Booking.objects.count(), 2)

    def test_cancel_booking_view(self):
        """Cek apakah cancel booking ubah status jadi cancelled"""
        response = self.client.get(reverse('cancel_booking', args=[self.booking.id]))
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')
