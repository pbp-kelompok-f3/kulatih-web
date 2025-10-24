from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import ForumPost, Vote, Comment

# ================== Helpers ==================
def _is_ajax(request):
    # fetch() kita selalu kirimkan header ini
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _vote_payload(post, user):
    score = post.votes.aggregate(total=Sum("value"))["total"] or 0
    user_vote = 0
    if user.is_authenticated:
        user_vote = (
            post.votes.filter(user=user)
            .values_list("value", flat=True)
            .first()
            or 0
        )
    return {"ok": True, "score": score, "user_vote": user_vote}


def _node_from_comment(c, user_id=None):
    """Konversi Comment -> node dict (tanpa children)."""
    return {
        "id": c.id,
        "author": c.display_name(),
        "author_id": c.author_id,
        "content": c.content,
        "created_iso": timezone.localtime(c.created_at).isoformat(),
        "created": timezone.localtime(c.created_at).strftime("%d %b %Y %H:%M"),
        "parent": c.parent_id,
        "replies": [],
        "replies_count": 0,
        "is_owner": bool(user_id and c.author_id == user_id),
    }


def _build_comment_tree(post, user):
    """Bangun tree dari semua komentar aktif, hitung replies_count per node."""
    all_comments = list(
        Comment.objects.filter(post=post, is_active=True)
        .select_related("author")
        .order_by("created_at")
    )

    nodes = {
        c.id: _node_from_comment(c, user.id if user.is_authenticated else None)
        for c in all_comments
    }

    roots = []
    for c in all_comments:
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id]["replies"].append(node)
        else:
            roots.append(node)

    def dfs_count(n):
        total = 0
        for ch in n["replies"]:
            total += 1 + dfs_count(ch)
        n["replies_count"] = total
        return total

    for r in roots:
        dfs_count(r)

    return roots, len(all_comments)


# ================== Posts ==================
def post_list(request):
    """List post + filter sederhana (q & mine)."""
    q = (request.GET.get("q") or "").strip()
    mine = request.GET.get("mine") == "1"

    posts = (
        ForumPost.objects.select_related("author")
        .prefetch_related("votes")
        .annotate(active_comments=Count("comments", filter=Q(comments__is_active=True)))
        .order_by("-created_at")
    )

    if q:
        posts = posts.filter(
            Q(content__icontains=q) | Q(author__username__icontains=q)
        )
    if mine and request.user.is_authenticated:
        posts = posts.filter(author=request.user)

    for p in posts:
        p.local_created = timezone.localtime(p.created_at)

    return render(
        request,
        "forum/post_list.html",
        {"posts": posts, "q": q, "mine": mine},
    )


@login_required
@require_POST
def create_post(request):
    content = (request.POST.get("content") or "").strip()
    if not content:
        messages.error(request, "Content is required.")
        return redirect("forum:post_list")
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
            vote.delete()  # toggle off
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
            vote.delete()  # toggle off
        else:
            vote.value = Vote.DOWN
            vote.save(update_fields=["value"])
    if _is_ajax(request):
        return JsonResponse(_vote_payload(post, request.user))
    return redirect("forum:post_list")


@login_required
def delete_post(request, post_id):
    """Hanya author yang boleh delete. POST-only, return JSON."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    post = get_object_or_404(ForumPost, id=post_id)

    # hard rule: hanya author yang bisa delete
    if request.user.id != post.author_id:
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    post.delete()  # CASCADE ke comments & votes
    return JsonResponse({"ok": True, "id": post_id})


@login_required
@require_POST
def edit_post(request, post_id):
    """Edit konten post. Boleh oleh author atau staff (sesuai kesepakatan)."""
    post = get_object_or_404(ForumPost, id=post_id)
    if not (request.user.is_staff or request.user == post.author):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse({"ok": False, "error": "empty content"}, status=400)
    post.content = content
    post.save(update_fields=["content"])
    return JsonResponse({"ok": True, "content": post.content})


# ================== Comments (reply-only) ==================
@never_cache
def comment_list(request, post_id):
    if request.method != "GET":
        return HttpResponseBadRequest("GET only")
    post = get_object_or_404(ForumPost, id=post_id)
    roots, total = _build_comment_tree(post, request.user)
    resp = JsonResponse({"ok": True, "items": roots, "count": total})
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"
    return resp


@login_required
@require_POST
def comment_add(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    content = (request.POST.get("content") or "").strip()
    parent_id = request.POST.get("parent")
    if not content:
        return JsonResponse({"ok": False, "error": "empty content"}, status=400)

    parent = None
    if parent_id:
        parent = get_object_or_404(
            Comment, id=parent_id, post=post, is_active=True
        )

    c = Comment.objects.create(
        post=post,
        author=request.user,
        name=request.user.get_username(),
        content=content,
        parent=parent,
    )
    node = _node_from_comment(c, request.user.id)
    return JsonResponse({"ok": True, "item": node})
