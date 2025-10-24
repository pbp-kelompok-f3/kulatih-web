from __future__ import annotations
import os
from django.test import TestCase, Client, override_settings
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.conf import settings

from .models import ForumPost, Vote, Comment, CommentVote

User = get_user_model()

# ========= Helpers =========
def url_or_skip(testcase: TestCase, name: str, *args, **kwargs) -> str:
    """
    Balikkan reverse URL, kalau belum terdaftar -> skip test ini.
    Membantu supaya test tidak error ketika suatu route belum di-include.
    """
    try:
        return reverse(name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        testcase.skipTest(f"URL name '{name}' belum dikonfigurasi.")

def has_admin():
    return "django.contrib.admin" in settings.INSTALLED_APPS


# ========= Base data =========
@override_settings(USE_TZ=True)
class BaseSetup(TestCase):
    def setUp(self):
        self.client = Client()

        self.alice = User.objects.create_user("alice", password="pass")
        self.bob   = User.objects.create_user("bob", password="pass")
        self.staff = User.objects.create_user("staff", password="pass", is_staff=True)

        self.post = ForumPost.objects.create(author=self.alice, content="Halo KuLatih!")
        # 2 komentar (c1 root, c2 reply ke c1)
        self.c1 = Comment.objects.create(post=self.post, author=self.bob, content="Mantap!")
        self.c2 = Comment.objects.create(post=self.post, author=self.alice, content="Balas", parent=self.c1)


# ========= Model tests =========
class ForumModelTests(BaseSetup):
    def test_post_score_and_vote_flip(self):
        self.assertEqual(self.post.score, 0)
        Vote.objects.create(post=self.post, user=self.bob, value=Vote.UP)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)

        # flip suara
        Vote.objects.filter(post=self.post, user=self.bob).delete()
        Vote.objects.create(post=self.post, user=self.bob, value=Vote.DOWN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, -1)

    def test_vote_unique_per_user_per_post(self):
        Vote.objects.create(post=self.post, user=self.alice, value=Vote.UP)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(post=self.post, user=self.alice, value=Vote.UP)

    def test_comment_vote_unique_per_user_per_comment(self):
        CommentVote.objects.create(comment=self.c1, user=self.alice, value=CommentVote.UP)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CommentVote.objects.create(comment=self.c1, user=self.alice, value=CommentVote.DOWN)

    def test_comment_score_and_display_name_and_str(self):
        self.assertEqual(self.c1.score, 0)
        CommentVote.objects.create(comment=self.c1, user=self.alice, value=CommentVote.UP)
        self.c1.refresh_from_db()
        self.assertEqual(self.c1.score, 1)
        # display_name: prefer username, fallback ke name, lalu "Anon"
        self.assertEqual(self.c1.display_name(), "bob")
        s = str(self.c1)
        self.assertIn("Comment(", s)
        self.assertIn("bob", s)

    def test_comment_parent_replies_and_ordering(self):
        # parent/child link
        self.assertEqual(self.c2.parent_id, self.c1.id)
        self.assertIn(self.c2, list(self.c1.replies.all()))
        # ordering default: Comment ascending by created_at
        c3 = Comment.objects.create(post=self.post, author=self.alice, content="Urutan 3")
        self.assertLessEqual(self.c1.created_at, self.c2.created_at)
        self.assertLessEqual(self.c2.created_at, c3.created_at)

    def test_post_str_and_ordering(self):
        other = ForumPost.objects.create(author=self.alice, content="Post kedua")
        posts = list(ForumPost.objects.all())  # Meta.ordering = ['-created_at']
        self.assertEqual(posts[0].id, other.id)  # newest first
        s = str(self.post)
        self.assertIn("alice", s)
        self.assertIn(self.post.content[:5], s)

    def test_delete_post_cascade_comments_and_votes(self):
        Vote.objects.create(post=self.post, user=self.bob, value=Vote.UP)
        cid = self.c1.id
        self.post.delete()
        self.assertFalse(Comment.objects.filter(id=cid).exists())
        self.assertFalse(Vote.objects.exists())


# ========= Admin read-only tests =========
class ForumAdminReadOnlyTests(BaseSetup):
    def setUp(self):
        super().setUp()
        if not has_admin():
            self.skipTest("Admin site tidak diaktifkan.")
        # user staf viewer -> hanya view permissions
        self.viewer = User.objects.create_user("viewer", password="pass", is_staff=True)
        perm_codes = ["view_forumpost", "view_comment", "view_vote", "view_commentvote"]
        self.viewer.user_permissions.set(Permission.objects.filter(codename__in=perm_codes))

    def test_admin_list_forumpost_no_add(self):
        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_forumpost_changelist")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b">Add ", res.content)  # tombol Add tidak ada

    def test_admin_change_readonly_hide_save_delete(self):
        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_forumpost_change", args=[self.post.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        # tidak ada tombol save / delete
        self.assertNotIn(b'name="_save"', res.content)
        self.assertNotIn(b"Save and continue", res.content)
        self.assertNotIn(b"Delete", res.content)

    def test_admin_add_forbidden(self):
        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_forumpost_add")
        res = self.client.get(url)
        self.assertIn(res.status_code, [302, 403])  # tergantung middleware/admin perms
        res2 = self.client.post(url, {"content": "x"})
        self.assertIn(res2.status_code, [302, 403])


# ========= View tests (AJAX & HTML) =========
class ForumViewTests(BaseSetup):
    def test_post_list_ok(self):
        # Pastikan halaman list render OK (template tidak error)
        url = url_or_skip(self, "forum:post_list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "FORUM")

    def test_create_post_requires_login_then_success(self):
        create_url = url_or_skip(self, "forum:create_post")
        # tanpa login -> redirect/403
        res = self.client.post(create_url, {"content": "Anon post"})
        self.assertIn(res.status_code, [302, 403])

        # login -> sukses (boleh JSON atau redirect, tergantung implementasi)
        self.client.login(username="alice", password="pass")
        res2 = self.client.post(create_url, {"content": "By Alice"})
        self.assertIn(res2.status_code, [200, 302])
        self.assertTrue(ForumPost.objects.filter(content__icontains="By Alice").exists())

    def test_edit_post_only_author_or_staff(self):
        edit_url = url_or_skip(self, "forum:edit_post", self.post.pk)

        # non-author -> ditolak
        self.client.login(username="bob", password="pass")
        r = self.client.post(edit_url, {"content": "Hacked"})
        self.assertIn(r.status_code, [403, 404])

        # author -> boleh
        self.client.login(username="alice", password="pass")
        r2 = self.client.post(edit_url, {"content": "Edited by author"})
        self.assertIn(r2.status_code, [200, 302])
        self.post.refresh_from_db()
        self.assertIn("Edited by author", self.post.content)

        # staff -> boleh
        self.client.login(username="staff", password="pass")
        r3 = self.client.post(edit_url, {"content": "Edited by staff"})
        self.assertIn(r3.status_code, [200, 302])

    def test_delete_post_only_author(self):
        delete_url = url_or_skip(self, "forum:delete_post", self.post.pk)

        # bukan author -> 403/404, post masih ada
        self.client.login(username="bob", password="pass")
        r = self.client.post(delete_url)
        self.assertIn(r.status_code, [403, 404])
        self.assertTrue(ForumPost.objects.filter(id=self.post.id).exists())

        # author -> boleh hapus
        self.client.login(username="alice", password="pass")
        r2 = self.client.post(delete_url)
        self.assertIn(r2.status_code, [200, 302])
        self.assertFalse(ForumPost.objects.filter(id=self.post.id).exists())

    def test_upvote_downvote_flow_and_score_json(self):
        up_url   = url_or_skip(self, "forum:upvote",   self.post.pk)
        down_url = url_or_skip(self, "forum:downvote", self.post.pk)

        self.client.login(username="bob", password="pass")

        r1 = self.client.post(up_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r1.status_code, 200)
        js1 = r1.json()
        self.assertIn("score", js1)
        self.assertIn("user_vote", js1)

        r2 = self.client.post(down_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r2.status_code, 200)
        js2 = r2.json()
        self.assertIn("score", js2)
        self.assertIn("user_vote", js2)

    def test_comment_list_returns_tree(self):
        list_url = url_or_skip(self, "forum:comment_list", self.post.pk)
        r = self.client.get(list_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("ok", True))
        self.assertIn("count", data)
        self.assertIsInstance(data.get("items", []), list)

    def test_comment_add_and_reply_flow(self):
        add_url = url_or_skip(self, "forum:comment_add", self.post.pk)

        # harus login
        r = self.client.post(add_url, {"content": "Anon"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIn(r.status_code, [302, 403])

        # login & add root
        self.client.login(username="bob", password="pass")
        r2 = self.client.post(add_url, {"content": "Cmnt"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r2.status_code, 200)
        cid = r2.json().get("item", {}).get("id")
        self.assertIsNotNone(cid)

        # reply ke comment yg baru dibuat
        r3 = self.client.post(add_url, {"content": "Reply", "parent": cid}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json().get("item", {}).get("parent"), cid)
