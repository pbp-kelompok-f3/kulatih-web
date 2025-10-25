from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class ForumPost(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts"
    )
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} · {self.content[:30]}"

    @property
    def score(self) -> int:
        return self.votes.aggregate(total=Sum("value"))["total"] or 0


class Vote(models.Model):
    UP, DOWN = 1, -1
    VALUE_CHOICES = ((UP, "Upvote"), (DOWN, "Downvote"))

    post = models.ForeignKey(ForumPost, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="forum_votes", on_delete=models.CASCADE
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"], name="unique_vote_per_user_per_post"
            ),
        ]


class Comment(models.Model):
    post = models.ForeignKey(ForumPost, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="forum_comments",
    )
    name = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def display_name(self):
        return (self.author.get_username() if self.author else None) or (self.name or "Anon")

    def __str__(self) -> str:
        return f"Comment({self.id}) by {self.display_name()}"
