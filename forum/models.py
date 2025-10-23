from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ForumPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    likes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.author.username} - {self.content[:30]}"

    def like_post(self):
        """Tambah satu like ke posting"""
        self.likes += 1
        self.save()

    def unlike_post(self):
        """Kurangi satu like (kalau masih ada)"""
        if self.likes > 0:
            self.likes -= 1
            self.save()

