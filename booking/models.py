from django.db import models
from django.utils import timezone

class Booking(models.Model):
    user_name = models.CharField(max_length=100)
    coach_name = models.CharField(max_length=100)
    sport_type = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user_name} - {self.sport_type} ({self.date})"

    class Meta:
        ordering = ['-date', '-start_time']

    @staticmethod
    def is_conflict(coach_name, date, start_time, end_time):
        """Return True kalau ada booking lain yang bentrok untuk coach yang sama."""
        conflicts = Booking.objects.filter(
            coach_name=coach_name,
            date=date,
            status__in=['pending', 'confirmed']
        ).filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        return conflicts.exists()
