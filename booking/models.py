from django.db import models
from django.utils import timezone
from users.models import Coach, Member
from datetime import time as dtime


class Booking(models.Model):
    # --- Relasi (One-to-One) ---
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name="bookings")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="bookings")

    # --- Waktu & Lokasi ---
    location = models.CharField(max_length=255, default="-")
    date = models.DateField()
    start_time = models.TimeField(default=dtime(9, 0))
    end_time = models.TimeField(default=dtime(10, 0))

    # --- Status Booking ---
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('rescheduled', 'Rescheduled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date', '-start_time', '-created_at']

    def __str__(self):
        coach_name = (
            self.coach.user.get_full_name() or self.coach.user.username
            if self.coach else "No Coach"
        )
        member_name = (
            self.member.user.get_full_name() or self.member.user.username
            if self.member else "No Member"
        )
        return f"{member_name} with {coach_name} on {self.date} {self.start_time}-{self.end_time}"

    # ---------- UTIL: Deteksi Overlap ----------
    @staticmethod
    def _is_overlap(a_start, a_end, b_start, b_end):
        """Dua rentang waktu overlap kalau: a_start < b_end dan a_end > b_start"""
        return (a_start < b_end) and (a_end > b_start)

    @staticmethod
    def is_conflict(coach, date, start_time, end_time, exclude_booking_id=None):
        """Cek apakah coach sudah punya booking aktif di waktu yang sama"""
        qs = Booking.objects.filter(
            coach=coach,
            date=date,
            status__in=['pending', 'confirmed', 'rescheduled']
        )
        if exclude_booking_id:
            qs = qs.exclude(id=exclude_booking_id)

        for b in qs.only('start_time', 'end_time'):
            if Booking._is_overlap(start_time, end_time, b.start_time, b.end_time):
                return True
        return False

    # ---------- UTIL: Reschedule ----------
    def reschedule(self, new_date, new_start_time, new_end_time):
        """Reschedule booking ke tanggal/jam baru."""
        if new_date < timezone.localdate():
            raise ValueError("Tidak bisa reschedule ke tanggal yang sudah lewat")
        if new_start_time >= new_end_time:
            raise ValueError("Jam mulai harus lebih kecil dari jam selesai")

        # Cek bentrok untuk coach
        if Booking.is_conflict(
            coach=self.coach, date=new_date,
            start_time=new_start_time, end_time=new_end_time,
            exclude_booking_id=self.id
        ):
            raise ValueError(f"Coach {self.coach.user.get_full_name()} sudah punya booking yang bentrok")

        self.date = new_date
        self.start_time = new_start_time
        self.end_time = new_end_time
        self.status = 'rescheduled'
        self.save()
