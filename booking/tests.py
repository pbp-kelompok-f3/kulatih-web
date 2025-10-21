from django.test import TestCase, Client
from django.urls import reverse
from .models import Booking
import datetime
import json

class BookingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.booking = Booking.objects.create(
            user_name='Alice',
            coach_name='Coach Bob',
            sport_type='Yoga',
            date=datetime.date.today(),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )

    def test_conflict_booking(self):
        """Coba buat booking baru dengan waktu yang bentrok."""
        data = {
            "user_name": "John",
            "coach_name": "Coach Bob",  # sama coach
            "sport_type": "Yoga",
            "date": str(datetime.date.today()),
            "start_time": "09:30",  # bentrok
            "end_time": "10:30"
        }
        response = self.client.post(reverse('booking_create'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertIn('sudah punya jadwal', response.json()['error'])
