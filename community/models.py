from django.db import models

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Community(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    short_description = models.CharField(max_length=200)
    full_description = models.TextField()
    profile_image_url = models.URLField(blank=True)  # gambar via link
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communities_created')

    def members_count(self):
        return self.memberships.count()

    def __str__(self):
        return self.name


class Membership(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('community', 'user')  # satu user satu membership per community

    def __str__(self):
        return f'{self.user} in {self.community} ({self.role})'


class Message(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # chat naik berurutan

    def __str__(self):
        return f'{self.sender} @ {self.community}: {self.text[:30]}'

