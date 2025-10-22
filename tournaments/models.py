from django.db import models
import uuid
from users.models import Coach, Member

class Tournament(models.Model):
    CATEGORY_CHOICES = [
        ('Futsal', 'Futsal'),
        ('Basket', 'Basket'),
        ('Voli', 'Voli'),
        ('Badminton', 'Badminton'),
        ('Tenis Meja', 'Tenis Meja'),
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
