from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member')

    profile_photo = models.URLField(blank=True, null=True)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username
    

class Coach(models.Model):
    SPORT_CHOICES = [
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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coach')

    profile_photo = models.URLField(blank=True, null=True)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    
    sport = models.CharField(max_length=20, choices=SPORT_CHOICES, default='other')
    hourly_fee = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username
