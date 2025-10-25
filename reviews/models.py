# reviews/models.py (punya kamu)
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from users.models import Coach, Member

User = settings.AUTH_USER_MODEL

class Review(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name="received_reviews")
    reviewer = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="written_reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["coach", "reviewer"], name="unique_reviewer_coach_once")
        ]

    def __str__(self):
        return f"r{self.id} {self.reviewer_id}->{self.coach_id} ★{self.rating}"
