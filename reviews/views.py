import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage
from django.db import IntegrityError
from django.db.models import Avg, Count
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.shortcuts import render


from .models import Review
from users.models import Coach, Member

User = get_user_model()


# READ
@require_GET
def coach_reviews_json(request, coach_id):
    """
    List review suatu coach + statistik & pagination.
    Sinkron dengan users: coach_id bertipe UUID.
    """
    coach = get_object_or_404(Coach, pk=coach_id)

    sort = (request.GET.get("sort") or "").lower()
    if   sort == "highest": order_by = "-rating"
    elif sort == "lowest":  order_by = "rating"
    else:                   order_by = "-created_at"  # DEFAULT: terbaru di atas

    qs = (
        Review.objects
        .filter(coach=coach)
        .select_related("reviewer__user")
        .order_by(order_by, "-id")  # tie-breaker stabil
    )
    
    stats = qs.aggregate(avg=Avg("rating"), total=Count("id"))

    # user login -> member_id untuk flag is_owner
    try:
        me_member_id = Member.objects.get(user=request.user).id
    except Exception:
        me_member_id = None

    # pagination
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get("page_size", 10))
    except ValueError:
        page_size = 10
    page_size = max(1, min(page_size, 50))

    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    items = []
    for r in page_obj.object_list:
        reviewer_username = getattr(getattr(r.reviewer, "user", None), "username", str(r.reviewer_id))
        items.append({
            "id": str(r.id),                        
            "reviewer_id": str(r.reviewer_id),
            "reviewer_username": reviewer_username,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
            "is_owner": (me_member_id == r.reviewer_id),
        })

    coach_username = getattr(getattr(coach, "user", None), "username", str(coach.id))
    data = {
        "coach": {"id": str(coach.id), "username": coach_username},
        "stats": {"avg": stats["avg"], "total": stats["total"]},
        "sort": sort,
        "pagination": {
            "page": page_obj.number,
            "page_size": page_size,
            "total_pages": paginator.num_pages,
            "total_items": paginator.count,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        },
        "items": items,
    }
    return JsonResponse(data, status=200)


@require_GET
def review_detail_json(request, review_id: int) -> JsonResponse:
    r = get_object_or_404(
        Review.objects.select_related("reviewer__user", "coach__user"),
        pk=review_id,
    )

    # flag owner
    try:
        me_member_id = Member.objects.get(user=request.user).id
    except Exception:
        me_member_id = None

    reviewer_username = getattr(getattr(r.reviewer, "user", None), "username", str(r.reviewer_id))
    coach_username = getattr(getattr(r.coach, "user", None), "username", str(r.coach_id))

    return JsonResponse({
        "id": str(r.id),
        "coach": {"id": str(r.coach_id), "username": coach_username},
        "reviewer": {"id": str(r.reviewer_id), "username": reviewer_username},
        "rating": r.rating,
        "comment": r.comment,
        "created_at": r.created_at.isoformat(),
        "is_owner": (me_member_id == r.reviewer_id),
    }, status=200)


# CREATE
@login_required
@require_POST
def create_review_json(request, coach_id):
    """
    Buat review oleh Member terhadap Coach (coach_id = UUID).
    """
    coach = get_object_or_404(Coach, pk=coach_id)

    # larang self-review jika user adalah coach tsb
    coach_user_id = getattr(getattr(coach, "user", None), "id", None)
    if coach_user_id and coach_user_id == request.user.id:
        return JsonResponse({"error": "not_allowed"}, status=403)

    # user harus punya profile Member
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        return JsonResponse({"error": "member_profile_required"}, status=403)

    # parse body JSON
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    rating = payload.get("rating")
    comment = (payload.get("comment") or "").strip()

    # validasi rating 1..5 (integer)
    if isinstance(rating, str) and rating.isdigit():
        rating = int(rating)
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return JsonResponse({"error": "rating_must_be_int_1_5"}, status=400)

    try:
        obj = Review.objects.create(
            coach=coach,
            reviewer=member,
            rating=rating,
            comment=comment[:1000],
        )
    except IntegrityError:
        return JsonResponse({"error": "already_reviewed"}, status=400)

    return JsonResponse({
        "message": "created",
        "id": str(obj.id),
        "coach_id": str(coach.id),
        "reviewer_id": str(member.id),
        "rating": obj.rating,
        "comment": obj.comment,
        "created_at": obj.created_at.isoformat(),
    }, status=201)


# UPDATE
@login_required
@require_http_methods(["PATCH", "PUT", "POST"])
def update_review_json(request, review_id: int) -> JsonResponse:
    review = get_object_or_404(Review, pk=review_id)

    is_admin = request.user.is_staff or request.user.is_superuser
    owner_ok = False
    try:
        member = Member.objects.get(user=request.user)
        owner_ok = (review.reviewer_id == member.id)
    except Member.DoesNotExist:
        owner_ok = False

    if not (is_admin or owner_ok):
        return JsonResponse({"error": "forbidden"}, status=403)

    # parse body
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    rating = payload.get("rating", None)
    comment = payload.get("comment", None)

    changed_fields = []

    if rating is not None:
        if isinstance(rating, str) and rating.isdigit():
            rating = int(rating)
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            return JsonResponse({"error": "rating_must_be_int_1_5"}, status=400)
        review.rating = rating
        changed_fields.append("rating")

    if comment is not None:
        review.comment = (comment or "").strip()[:1000]
        changed_fields.append("comment")

    if changed_fields:
        review.save(update_fields=changed_fields)

    return JsonResponse({
        "message": "updated",
        "id": str(review.id),
        "rating": review.rating,
        "comment": review.comment,
    }, status=200)


# DELETE
@login_required
@require_http_methods(["DELETE", "POST"])
def delete_review_json(request, review_id: int) -> JsonResponse:
    review = get_object_or_404(Review, pk=review_id)

    is_admin = request.user.is_staff or request.user.is_superuser
    owner_ok = False
    try:
        member = Member.objects.get(user=request.user)
        owner_ok = (review.reviewer_id == member.id)
    except Member.DoesNotExist:
        owner_ok = False

    if not (is_admin or owner_ok):
        return JsonResponse({"error": "forbidden"}, status=403)

    review.delete()
    return JsonResponse({"message": "deleted", "id": str(review_id)}, status=200)

@require_GET
def review_detail_page(request, review_id: int):
    r = get_object_or_404(
        Review.objects.select_related("reviewer__user", "coach__user"),
        pk=review_id,
    )
    # flag owner
    try:
        me_member_id = Member.objects.get(user=request.user).id
    except Exception:
        me_member_id = None
    is_owner = (me_member_id == r.reviewer_id)

    ctx = {
        "review": r,
        "is_owner": is_owner,
        "coach_username": getattr(getattr(r.coach, "user", None), "username", str(r.coach_id)),
        "reviewer_username": getattr(getattr(r.reviewer, "user", None), "username", str(r.reviewer_id)),
    }
    return render(request, "review_detail.html", ctx)
