from django.db import models
from django.utils import timezone
from users.models import Coach, Member


class Booking(models.Model):
    coach = models.ManyToManyField(Coach, blank=True)
    member = models.ManyToManyField(Member, blank=True)
    date = models.DateField()

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
        ordering = ['-date', '-created_at']

    def __str__(self):
        coach_names = ", ".join(c.name for c in self.coach.all())
        member_names = ", ".join(m.name for m in self.member.all())
        return f"{member_names} with {coach_names} on {self.date}"

    @staticmethod
    def is_conflict(coach, date):
        """
        Return True kalau coach sudah punya booking aktif
        di tanggal yang sama.
        """
        conflicts = Booking.objects.filter(
            coach=coach,
            date=date,
            status__in=['pending', 'confirmed']
        )
        return conflicts.exists()

    def reschedule(self, new_date):
        """
        Reschedule booking ke tanggal baru.
        """
        if new_date < timezone.now().date():
            raise ValueError("Tidak bisa reschedule ke tanggal yang sudah lewat")

        # Periksa bentrok untuk tiap coach di booking ini
        for c in self.coach.all():
            if Booking.is_conflict(c, new_date):
                raise ValueError(f"Coach {c.name} sudah punya booking di tanggal {new_date}")

        self.date = new_date
        self.status = 'rescheduled'
        self.save()
