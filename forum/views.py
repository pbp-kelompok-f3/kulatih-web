from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone  # ← TAMBAHKAN INI

from .models import ForumPost, Vote

def post_list(request):
    posts = ForumPost.objects.select_related("author").prefetch_related("votes")
    for p in posts:
        # nilai vote user
        if request.user.is_authenticated:
            v = p.votes.filter(user=request.user).values_list("value", flat=True).first()
            p.user_vote_value = v or 0
        else:
            p.user_vote_value = 0

        # Waktu lokal Jakarta (WIB, AM/PM tetap)
        # Kalau settings.TIME_ZONE sudah "Asia/Jakarta", cukup: timezone.localtime(p.created_at)
        p.local_created = timezone.localtime(
            p.created_at, timezone.get_fixed_timezone(7 * 60)
        )
    return render(request, "forum/post_list.html", {"posts": posts})

@login_required
@require_POST
def create_post(request):
    content = request.POST.get("content", "").strip()
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
    v, created = Vote.objects.get_or_create(
        post=post, user=request.user, defaults={"value": Vote.UP}
    )
    if not created:
        if v.value == Vote.UP:
            v.delete()  # klik lagi = unvote
        else:
            v.value = Vote.UP  # dari down -> up
            v.save(update_fields=["value"])
    return redirect("forum:post_list")


@login_required
@require_POST
def downvote(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    v, created = Vote.objects.get_or_create(
        post=post, user=request.user, defaults={"value": Vote.DOWN}
    )
    if not created:
        if v.value == Vote.DOWN:
            v.delete()  # klik lagi = unvote
        else:
            v.value = Vote.DOWN  # dari up -> down
            v.save(update_fields=["value"])
    return redirect("forum:post_list")


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)

    allowed = request.user.is_staff or request.user == post.author
    if not allowed:
        if _is_ajax(request):
            return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
        messages.error(request, "You are not allowed to delete this post.")
        return redirect("forum:post_list")

    post.delete()

    if _is_ajax(request):
        return JsonResponse({"ok": True, "post_id": post_id})

    messages.success(request, "Post deleted.")
    return redirect("forum:post_list")
