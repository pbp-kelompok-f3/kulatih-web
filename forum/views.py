from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone

from .models import ForumPost, Vote


# ---------- Helpers ----------
def _is_ajax(request):
    # Semua fetch() di template sudah mengirim header ini
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _vote_payload(post, user):
    """Hitung score & vote user saat ini untuk response AJAX."""
    score = post.votes.aggregate(total=Sum("value"))["total"] or 0
    user_vote = 0
    if user.is_authenticated:
        user_vote = post.votes.filter(user=user).values_list("value", flat=True).first() or 0
    return {"ok": True, "score": score, "user_vote": user_vote}


# ---------- Views ----------
def post_list(request):
    posts = (
        ForumPost.objects
        .select_related("author")
        .prefetch_related("votes")
        .order_by("-created_at")
    )

    # Sematkan nilai vote user + waktu lokal (WIB) ke tiap objek untuk template
    for p in posts:
        if request.user.is_authenticated:
            v = p.votes.filter(user=request.user).values_list("value", flat=True).first()
            p.user_vote_value = v or 0
        else:
            p.user_vote_value = 0

        # Jika TIME_ZONE sudah Asia/Jakarta, cukup timezone.localtime(p.created_at)
        try:
            p.local_created = timezone.localtime(p.created_at)
        except Exception:
            # Fallback manual ke UTC+7 jika settings belum Asia/Jakarta
            p.local_created = timezone.localtime(p.created_at, timezone.get_fixed_timezone(7 * 60))

    return render(request, "forum/post_list.html", {"posts": posts})


@login_required
@require_POST
def create_post(request):
    content = (request.POST.get("content") or "").strip()
    if not content:
        messages.error(request, "Content is required.")
    else:
        ForumPost.objects.create(author=request.user, content=content)
        messages.success(request, "Post created.")
    return redirect("forum:post_list")


@login_required
@require_POST
def upvote(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)

    vote, created = Vote.objects.get_or_create(
        post=post, user=request.user, defaults={"value": Vote.UP}
    )
    if not created:
        if vote.value == Vote.UP:
            # klik lagi: batalkan
            vote.delete()
        else:
            vote.value = Vote.UP
            vote.save(update_fields=["value"])

    if _is_ajax(request):
        return JsonResponse(_vote_payload(post, request.user))
    return redirect("forum:post_list")


@login_required
@require_POST
def downvote(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)

    vote, created = Vote.objects.get_or_create(
        post=post, user=request.user, defaults={"value": Vote.DOWN}
    )
    if not created:
        if vote.value == Vote.DOWN:
            # klik lagi: batalkan
            vote.delete()
        else:
            vote.value = Vote.DOWN
            vote.save(update_fields=["value"])

    if _is_ajax(request):
        return JsonResponse(_vote_payload(post, request.user))
    return redirect("forum:post_list")


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)

    if not (request.user.is_staff or request.user == post.author):
        if _is_ajax(request):
            return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
        messages.error(request, "You are not allowed to delete this post.")
        return redirect("forum:post_list")

    post.delete()

    if _is_ajax(request):
        return JsonResponse({"ok": True, "post_id": post_id})

    messages.success(request, "Post deleted.")
    return redirect("forum:post_list")
