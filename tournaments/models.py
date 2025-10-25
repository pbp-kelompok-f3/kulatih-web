from django.db import models
import uuid
from datetime import date
from users.models import Coach, Member

class Tournament(models.Model):
    CATEGORY_CHOICES = [
        ('gym', 'Gym & Fitness'),
        ('football', 'Football'),
        ('futsal', 'Futsal'),
        ('basketball', 'Basketball'),
        ('tennis', 'Tennis'),
        ('badminton', 'Badminton'),
        ('swimming', 'Swimming'),
        ('yoga', 'Yoga'),
        ('martial_arts', 'Martial Arts'),
        ('golf', 'Golf'),
        ('volleyball', 'Volleyball'),
        ('running', 'Running'),
        ('other', 'Other'),
    ]

    pembuatTournaments = models.ForeignKey(Coach, on_delete=models.CASCADE)
    pesertaTournaments = models.ManyToManyField(Member, blank=True)
    tipeTournaments = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    namaTournaments = models.CharField(max_length=100)
    tanggalTournaments = models.DateField()
    lokasiTournaments = models.CharField(max_length=200)
    deskripsiTournaments = models.TextField()
    posterTournaments = models.URLField(max_length=200)
    flagTournaments = models.BooleanField(default=True)
    idTournaments = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.namaTournaments

    @property
    def is_active(self):
        return self.tanggalTournaments >= date.today()

    def save(self, *args, **kwargs):
        if self.tanggalTournaments < date.today():
            self.flagTournaments = False
        else:
            self.flagTournaments = True
        super().save(*args, **kwargs)
