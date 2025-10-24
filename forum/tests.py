# forum/tests.py
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import ForumPost, Vote, Comment

User = get_user_model()


def ajax_headers():
    return {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class BaseSetup(TestCase):
    def setUp(self):
        self.client = Client()
        self.alice = User.objects.create_user("alice", password="pass")
        self.bob = User.objects.create_user("bob", password="pass")
        self.staff = User.objects.create_user("staff", password="pass", is_staff=True)

        self.post = ForumPost.objects.create(author=self.alice, content="Halo KuLatih!")
        # 2 komentar (c1 root, c2 reply ke c1)
        self.c1 = Comment.objects.create(post=self.post, author=self.bob, content="Mantap!")
        self.c2 = Comment.objects.create(post=self.post, author=self.alice, content="Balas", parent=self.c1)


# =========================
# Models coverage
# =========================
class ForumModelTests(BaseSetup):
    def test_post_str_and_ordering(self):
        newer = ForumPost.objects.create(author=self.alice, content="Terbaru")
        posts = list(ForumPost.objects.all())
        self.assertEqual(posts[0].id, newer.id)
        self.assertIn("alice", str(self.post))
        self.assertIn(self.post.content[:10], str(self.post))

    def test_vote_unique_and_score_toggle(self):
        # score awal
        self.assertEqual(self.post.score, 0)

        # unique per (post,user)
        Vote.objects.create(post=self.post, user=self.bob, value=Vote.UP)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(post=self.post, user=self.bob, value=Vote.DOWN)

        # ubah suara (hapus & buat lagi) mempengaruhi agregasi score
        Vote.objects.filter(post=self.post, user=self.bob).delete()
        Vote.objects.create(post=self.post, user=self.bob, value=Vote.DOWN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, -1)

    def test_comment_relations_and_str(self):
        # parent/child link + ordering created_at asc
        self.assertEqual(self.c2.parent_id, self.c1.id)
        self.assertIn(self.c2, list(self.c1.replies.all()))
        self.assertLessEqual(self.c1.created_at, self.c2.created_at)
        self.assertIn("Comment(", str(self.c1))

    def test_display_name_and_created_at(self):
        # display_name memilih username
        self.assertEqual(self.c1.display_name(), "bob")
        # created_at ada dan tz-aware
        self.assertTrue(timezone.is_aware(self.c1.created_at))


# =========================
# Views coverage (HTML + JSON)
# =========================
class ForumViewTests(BaseSetup):
    def test_post_list_renders_and_sets_local_created(self):
        url = reverse("forum:post_list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        # view set p.local_created untuk setiap post
        for p in res.context["posts"]:
            self.assertTrue(hasattr(p, "local_created"))

    def test_post_list_filter_q_and_mine(self):
        # tambah 1 post lain oleh bob
        ForumPost.objects.create(author=self.bob, content="Postingan Bob keren")

        # filter q=Bob
        url = reverse("forum:post_list")
        res = self.client.get(url, {"q": "Bob"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any("Bob" in (p.author.username or "") for p in res.context["posts"]))

        # filter mine=1 (harus login)
        self.client.login(username="alice", password="pass")
        res2 = self.client.get(url, {"mine": "1"})
        self.assertTrue(all(p.author_id == self.alice.id for p in res2.context["posts"]))

    def test_create_post_requires_login_and_success(self):
        url = reverse("forum:create_post")
        # tanpa login -> redirect/forbidden
        r = self.client.post(url, {"content": "x"})
        self.assertIn(r.status_code, [302, 403])

        # login -> ok & redirect
        self.client.login(username="alice", password="pass")
        r2 = self.client.post(url, {"content": "By Alice"})
        self.assertIn(r2.status_code, [302, 200])
        self.assertTrue(ForumPost.objects.filter(content__icontains="By Alice").exists())

    def test_upvote_then_toggle_and_downvote_paths(self):
        up_url = reverse("forum:upvote", args=[self.post.pk])
        down_url = reverse("forum:downvote", args=[self.post.pk])
        self.client.login(username="bob", password="pass")

        # upvote (AJAX)
        r1 = self.client.post(up_url, **ajax_headers())
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json().get("user_vote"), 1)

        # upvote lagi -> toggle off (score turun)
        r2 = self.client.post(up_url, **ajax_headers())
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json().get("user_vote"), 0)

        # downvote
        r3 = self.client.post(down_url, **ajax_headers())
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json().get("user_vote"), -1)

    def test_delete_post_method_guard_and_author_only(self):
        url = reverse("forum:delete_post", args=[self.post.pk])

        # GET -> 405 json
        self.client.login(username="alice", password="pass")
        r_get = self.client.get(url, **ajax_headers())
        self.assertEqual(r_get.status_code, 405)

        # non-author -> 403
        self.client.login(username="bob", password="pass")
        r_forbidden = self.client.post(url, **ajax_headers())
        self.assertEqual(r_forbidden.status_code, 403)

        # author -> OK
        self.client.login(username="alice", password="pass")
        r_ok = self.client.post(url, **ajax_headers())
        self.assertEqual(r_ok.status_code, 200)
        self.assertFalse(ForumPost.objects.filter(id=self.post.id).exists())

    def test_edit_post_author_or_staff_and_payload(self):
        url = reverse("forum:edit_post", args=[self.post.pk])

        # bob (bukan author, bukan staff) -> 403
        self.client.login(username="bob", password="pass")
        r_forbidden = self.client.post(url, {"content": "Hacked"}, **ajax_headers())
        self.assertEqual(r_forbidden.status_code, 403)

        # author -> ok
        self.client.login(username="alice", password="pass")
        r_ok = self.client.post(url, {"content": "Edited by author"}, **ajax_headers())
        self.assertEqual(r_ok.status_code, 200)
        self.assertEqual(r_ok.json()["content"], "Edited by author")

        # staff -> ok
        self.client.login(username="staff", password="pass")
        r_staff = self.client.post(url, {"content": "Edited by staff"}, **ajax_headers())
        self.assertEqual(r_staff.status_code, 200)
        self.assertEqual(r_staff.json()["content"], "Edited by staff")

        # empty -> 400
        r_empty = self.client.post(url, {"content": ""}, **ajax_headers())
        self.assertEqual(r_empty.status_code, 400)

    def test_comment_list_get_and_not_get(self):
        list_url = reverse("forum:comment_list", args=[self.post.pk])

        # GET -> ok, shape tree
        r = self.client.get(list_url, **ajax_headers())
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("items", data)
        self.assertIn("count", data)

        # POST -> 400 (guard)
        r_bad = self.client.post(list_url, **ajax_headers())
        self.assertEqual(r_bad.status_code, 400)

    def test_comment_add_root_and_reply_and_invalid_parent(self):
        add_url = reverse("forum:comment_add", args=[self.post.pk])

        # must login
        r = self.client.post(add_url, {"content": "Anon"}, **ajax_headers())
        self.assertIn(r.status_code, [302, 403])

        # login, add root
        self.client.login(username="bob", password="pass")
        r2 = self.client.post(add_url, {"content": "Root Cmnt"}, **ajax_headers())
        self.assertEqual(r2.status_code, 200)
        root_id = r2.json()["item"]["id"]

        # reply to root
        r3 = self.client.post(add_url, {"content": "Reply", "parent": root_id}, **ajax_headers())
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["item"]["parent"], root_id)

        # invalid parent (404)
        r4 = self.client.post(add_url, {"content": "x", "parent": 999999}, **ajax_headers())
        self.assertEqual(r4.status_code, 404)


# =========================
# Admin coverage (read-only)
# =========================
class ForumAdminTests(BaseSetup):
    def setUp(self):
        super().setUp()
        # staff viewer dengan permission view_* biar bisa akses changelist
        self.viewer = User.objects.create_user("viewer", password="pass", is_staff=True)
        self.viewer.user_permissions.set(
            Permission.objects.filter(
                codename__in=[
                    "view_forumpost",
                    "view_comment",
                    "view_vote",
                ]
            )
        )

    def test_admin_forumpost_changelist_readonly(self):
        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_forumpost_changelist")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        # tombol Add tidak ada (read-only)
        self.assertNotIn(b">Add ", res.content)

    def test_admin_forumpost_change_readonly_buttons_hidden(self):
        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_forumpost_change", args=[self.post.pk])
        res = self.client.get(url)
        this = res.content  # keep var to avoid linter remove
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b'name="_save"', res.content)       # save button
        self.assertNotIn(b"Save and continue", res.content)  # save&continue
        self.assertNotIn(b">Delete</a>", res.content)        # delete

    def test_admin_forumpost_add_forbidden(self):
        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_forumpost_add")
        # GET add page -> biasanya 403 (atau redirect tergantung middleware)
        res = self.client.get(url)
        self.assertIn(res.status_code, [302, 403])
        # POST add juga tidak boleh
        res2 = self.client.post(url, {"content": "x"})
        self.assertIn(res2.status_code, [302, 403])

    def test_admin_comment_changelist_and_readonly(self):
        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_comment_changelist")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        # tidak ada "Add"
        self.assertNotIn(b">Add ", res.content)

    def test_admin_vote_changelist_and_readonly(self):
        # buat 1 vote supaya tabel ada data
        Vote.objects.create(post=self.post, user=self.bob, value=Vote.UP)

        self.client.login(username="viewer", password="pass")
        url = reverse("admin:forum_vote_changelist")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"UP", res.content)
        # tidak ada "Add"
        self.assertNotIn(b">Add ", res.content)
