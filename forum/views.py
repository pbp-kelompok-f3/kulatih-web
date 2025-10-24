from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import Comment, CommentVote, ForumPost, Vote


# ---------------- Helpers ----------------
def _is_ajax(request):
    # header name yang dipakai fetch() kita adalah X-Requested-With
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _vote_payload(post, user):
    score = post.votes.aggregate(total=Sum("value"))["total"] or 0
    user_vote = 0
    if user.is_authenticated:
        user_vote = post.votes.filter(user=user).values_list("value", flat=True).first() or 0
    return {"ok": True, "score": score, "user_vote": user_vote}


def _user_comment_vote_map(post, user):
    if not user.is_authenticated:
        return {}
    pairs = (
        CommentVote.objects.filter(comment__post=post, user=user)
        .values_list("comment_id", "value")
    )
    return {cid: val for cid, val in pairs}


def _comment_node(c, vote_map, user_id):
    return {
        "id": c.id,
        "author": c.display_name(),
        "author_id": c.author_id,
        "content": c.content,
        "created": timezone.localtime(c.created_at).strftime("%d %b %Y %H:%M"),
        "parent": c.parent_id,
        "score": c.score,
        "user_vote": vote_map.get(c.id, 0),
        "is_owner": bool(user_id and c.author_id == user_id),
        "replies": [],
        "replies_count": 0,
    }


def _build_comment_tree(post, user):
    comments = list(
        Comment.objects.filter(post=post, is_active=True)
        .select_related("author")
        .order_by("created_at")
    )
    vote_map = _user_comment_vote_map(post, user)
    nodes = {c.id: _comment_node(c, vote_map, user.id if user.is_authenticated else None) for c in comments}
    roots = []
    for c in comments:
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id]["replies"].append(node)
        else:
            roots.append(node)

    def calc(n):
        total = 0
        for ch in n["replies"]:
            total += 1 + calc(ch)
        n["replies_count"] = total
        return total

    for r in roots:
        calc(r)

    return roots, len(comments)


# ---------------- Posts ----------------
def post_list(request):
    posts = (
        ForumPost.objects
        .select_related("author")
        .prefetch_related("votes")
        .annotate(active_comments=Count("comments", filter=Q(comments__is_active=True)))
        .order_by("-created_at")
    )
    for p in posts:
        p.local_created = timezone.localtime(p.created_at)
    return render(request, "forum/post_list.html", {"posts": posts})


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
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    post.delete()  # CASCADE ke komentar
    return JsonResponse({"ok": True})


@login_required
@require_POST
def edit_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if not (request.user.is_staff or request.user == post.author):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse({"ok": False, "error": "empty content"}, status=400)
    post.content = content
    post.save(update_fields=["content"])
    return JsonResponse({"ok": True, "content": post.content})


# ---------------- Comments API ----------------
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
        parent = get_object_or_404(Comment, id=parent_id, post=post, is_active=True)
    c = Comment.objects.create(
        post=post,
        author=request.user,
        name=request.user.get_username(),
        content=content,
        parent=parent,
    )
    node = _comment_node(c, {}, request.user.id)
    return JsonResponse({"ok": True, "item": node})


@login_required
@require_POST
def comment_edit(request, post_id, comment_id):
    """EDIT reply/comment via AJAX."""
    post = get_object_or_404(ForumPost, id=post_id)
    c = get_object_or_404(Comment, id=comment_id, post=post, is_active=True)

    if not (request.user.is_staff or c.author_id == request.user.id):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse({"ok": False, "error": "empty content"}, status=400)

    c.content = content
    c.save(update_fields=["content"])
    return JsonResponse({"ok": True, "content": c.content})


@login_required
@require_POST
def comment_delete(request, post_id, comment_id):
    post = get_object_or_404(ForumPost, id=post_id)
    c = get_object_or_404(Comment, id=comment_id, post=post, is_active=True)
    if not (request.user.is_staff or c.author_id == request.user.id):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    c.delete()  # CASCADE subtree
    return JsonResponse({"ok": True, "id": comment_id})


@login_required
@require_POST
def comment_vote(request, post_id, comment_id, action):
    # (Masih disediakan; di UI reply bisa di-nonaktifkan. Endpoint ini aman untuk dipakai/diabaikan.)
    get_object_or_404(ForumPost, id=post_id)
    c = get_object_or_404(Comment, id=comment_id, post_id=post_id, is_active=True)
    val = CommentVote.UP if action == "up" else CommentVote.DOWN
    vote, created = CommentVote.objects.get_or_create(
        comment=c, user=request.user, defaults={"value": val}
    )
    if not created:
        if vote.value == val:
            vote.delete()
        else:
            vote.value = val
            vote.save(update_fields=["value"])
    user_vote = (
        CommentVote.objects.filter(comment=c, user=request.user)
        .values_list("value", flat=True)
        .first()
        or 0
    )
    return JsonResponse({"ok": True, "score": c.score, "user_vote": user_vote})

@login_required
@require_POST
def comment_edit(request, post_id, comment_id):
    """Edit isi reply/comment (owner-only atau staff)."""
    post = get_object_or_404(ForumPost, id=post_id)
    c = get_object_or_404(Comment, id=comment_id, post=post, is_active=True)
    if not (request.user.is_staff or c.author_id == request.user.id):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)
    c.content = content
    c.save(update_fields=["content"])
    return JsonResponse({"ok": True, "content": c.content})