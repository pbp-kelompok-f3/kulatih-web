# bookings/models.py
from django.db import models
from django.utils import timezone
from users.models import Coach, Member
from datetime import datetime, time as dtime

class Booking(models.Model):
    coach = models.ManyToManyField(Coach, blank=True)
    member = models.ManyToManyField(Member, blank=True)

    date = models.DateField()
    start_time = models.TimeField(default=dtime(9, 0))         # ⬅️ jam mulai
    end_time   = models.TimeField(default=dtime(10, 0))         # ⬅️ jam selesai

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
        ordering = ['-date', '-start_time', '-created_at']  # ⬅️ urutkan juga pakai jam

    def __str__(self):
        coach_names = ", ".join(c.name for c in self.coach.all())
        member_names = ", ".join(m.name for m in self.member.all())
        return f"{member_names} with {coach_names} on {self.date} {self.start_time}-{self.end_time}"

    # ---------- Util untuk overlap time ----------
    @staticmethod
    def _is_overlap(a_start, a_end, b_start, b_end):
        """
        Dua rentang waktu overlap kalau: a_start < b_end dan a_end > b_start
        """
        return (a_start < b_end) and (a_end > b_start)

    @staticmethod
    def is_conflict(coach, date, start_time, end_time, exclude_booking_id=None):
        """
        True kalau coach punya booking aktif (pending/confirmed/rescheduled)
        di tanggal & rentang jam yang overlap.
        """
        qs = Booking.objects.filter(
            coach=coach, date=date,
            status__in=['pending', 'confirmed', 'rescheduled']
        )
        if exclude_booking_id:
            qs = qs.exclude(id=exclude_booking_id)

        for b in qs.only('start_time', 'end_time'):
            if Booking._is_overlap(start_time, end_time, b.start_time, b.end_time):
                return True
        return False

    def reschedule(self, new_date, new_start_time, new_end_time):
        """
        Reschedule booking ke tanggal/jam baru.
        """
        if new_date < timezone.localdate():
            raise ValueError("Tidak bisa reschedule ke tanggal yang sudah lewat")
        if new_start_time >= new_end_time:
            raise ValueError("Jam mulai harus lebih kecil dari jam selesai")

        # Periksa bentrok untuk tiap coach di booking ini
        for c in self.coach.all():
            if Booking.is_conflict(
                coach=c, date=new_date,
                start_time=new_start_time, end_time=new_end_time,
                exclude_booking_id=self.id
            ):
                raise ValueError(f"Coach {c.name} sudah punya booking yang bentrok")

        self.date = new_date
        self.start_time = new_start_time
        self.end_time = new_end_time
        self.status = 'rescheduled'
        self.save()
