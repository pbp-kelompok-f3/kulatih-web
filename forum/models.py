from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum

class ForumPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts")
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} · {self.content[:30]}"

    # SCORE total (upvote=+1, downvote=-1)
    @property
    def score(self):
        return self.votes.aggregate(total=Sum("value"))["total"] or 0

    # nilai vote user saat ini: 1, -1, atau 0
    def user_vote(self, user):
        if not getattr(user, "is_authenticated", False):
            return 0
        val = self.votes.filter(user=user).values_list("value", flat=True).first()
        return val or 0

class Vote(models.Model):
    UP = 1
    DOWN = -1
    VALUE_CHOICES = ((UP, "Upvote"), (DOWN, "Downvote"))

    post = models.ForeignKey(ForumPost, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="forum_votes", on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_vote_per_user_per_post"),
        ]
