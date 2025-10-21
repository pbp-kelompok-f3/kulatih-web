# reviews/views.py
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .models import Review

User = get_user_model()

def _can_user_review(user, coach):
    """
    HOOK VALIDASI — SEKARANG:
    - user harus login (ditangani @login_required)
    - user tidak boleh review dirinya sendiri

    NANTI (sinkron):
    - return user_has_completed_booking(user=user, coach=coach)
    - + cek role user==murid, coach==coach (ambil dari modul User/Coach)
    """
    return user.id != coach.id

@require_GET
def coach_reviews_json(request, coach_id):
    coach = get_object_or_404(User, pk=coach_id)
    qs = Review.objects.filter(coach=coach)
    return JsonResponse({
        "coach_id": coach.id,
        "coach_username": getattr(coach, "username", str(coach.id)),
        "stats": qs.aggregate(avg=Avg("rating"), total=Count("id")),
        "items": [{
            "id": r.id,
            "reviewer_id": r.reviewer_id,
            "reviewer_username": getattr(r.reviewer, "username", str(r.reviewer_id)),
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        } for r in qs]
    }, status=200)

@login_required
@require_POST
def create_review_json(request, coach_id):
    coach = get_object_or_404(User, pk=coach_id)
    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    rating = payload.get("rating")
    comment = (payload.get("comment") or "").strip()

    if not _can_user_review(request.user, coach):
        return JsonResponse({"error": "Not allowed"}, status=403)

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return JsonResponse({"error": "rating must be integer 1..5"}, status=400)

    try:
        obj = Review.objects.create(
            coach=coach, reviewer=request.user, rating=rating, comment=comment
        )
    except Exception as e:
        return JsonResponse({"error": "already_reviewed"}, status=400)

    return JsonResponse({
        "message": "created",
        "id": obj.id,
        "coach_id": coach.id,
        "rating": obj.rating,
        "comment": obj.comment,
        "created_at": obj.created_at.isoformat(),
    }, status=201)
