from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from reviews.models import Review

User = get_user_model()

class ReviewsApiTests(TestCase):
    def setUp(self):
        # akun dasar
        self.coach = User.objects.create_user(username="coach", password="x")
        self.user = User.objects.create_user(username="user", password="x")
        self.other = User.objects.create_user(username="other", password="x")
        self.admin = User.objects.create_user(username="admin", password="x", is_staff=True)

    # ------- helpers -------
    def login(self, who="user"):
        creds = {"user": ("user", "x"),
                 "coach": ("coach", "x"),
                 "other": ("other", "x"),
                 "admin": ("admin", "x")}[who]
        self.client.login(username=creds[0], password=creds[1])

    def create_review(self, reviewer, coach=None, rating=5, comment="ok"):
        return Review.objects.create(
            coach=coach or self.coach,
            reviewer=reviewer,
            rating=rating,
            comment=comment,
        )

    # ------- READ -------
    def test_list_empty_stats(self):
        url = reverse("reviews:coach_reviews_json", args=[self.coach.id])
        res = self.client.get(url).json()
        self.assertEqual(res["stats"]["total"], 0)
        self.assertIsNone(res["stats"]["avg"])

    def test_list_sorting_highest_lowest(self):
        self.create_review(self.user, rating=5)
        self.create_review(self.other, rating=2)
        url = reverse("reviews:coach_reviews_json", args=[self.coach.id])

        # highest
        res = self.client.get(url + "?sort=highest").json()
        self.assertEqual([item["rating"] for item in res["items"]], [5, 2])

        # lowest
        res = self.client.get(url + "?sort=lowest").json()
        self.assertEqual([item["rating"] for item in res["items"]], [2, 5])

    def test_pagination(self):
        # 12 reviews random (pakai users berbeda-beda)
        for i in range(12):
            u = User.objects.create_user(username=f"u{i}")
            self.create_review(u, rating=3)
        url = reverse("reviews:coach_reviews_json", args=[self.coach.id]) + "?page=2&page_size=5"
        res = self.client.get(url).json()
        self.assertEqual(res["pagination"]["page"], 2)
        self.assertEqual(len(res["items"]), 5)
        self.assertEqual(res["pagination"]["total_items"], 12)

    # ------- CREATE -------
    def test_create_success_once(self):
        self.login("user")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        res = self.client.post(url, data='{"rating":5,"comment":"gas"}',
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        # coba lagi → should fail (unique)
        res2 = self.client.post(url, data='{"rating":4}',
                                content_type="application/json")
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(Review.objects.filter(coach=self.coach, reviewer=self.user).count(), 1)

    def test_create_forbid_self_review(self):
        self.login("coach")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        res = self.client.post(url, data='{"rating":4}', content_type="application/json")
        self.assertEqual(res.status_code, 403)

    def test_create_invalid_rating(self):
        self.login("user")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        bad = self.client.post(url, data='{"rating":"abc"}', content_type="application/json")
        self.assertEqual(bad.status_code, 400)

    def test_create_invalid_json(self):
        self.login("user")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        bad = self.client.post(url, data='{not-json}', content_type="application/json")
        self.assertEqual(bad.status_code, 400)

    # ------- UPDATE -------
    def test_update_by_owner(self):
        r = self.create_review(self.user, rating=3)
        self.login("user")
        url = reverse("reviews:update_review_json", args=[r.id])
        res = self.client.patch(url, data='{"rating":5,"comment":"up"}',
                                content_type="application/json")
        self.assertEqual(res.status_code, 200)
        r.refresh_from_db()
        self.assertEqual(r.rating, 5)
        self.assertEqual(r.comment, "up")

    def test_update_forbidden_if_not_owner(self):
        r = self.create_review(self.user, rating=3)
        self.login("other")
        url = reverse("reviews:update_review_json", args=[r.id])
        res = self.client.patch(url, data='{"rating":4}', content_type="application/json")
        self.assertEqual(res.status_code, 403)

    def test_update_by_admin_allowed(self):
        r = self.create_review(self.user, rating=2)
        self.login("admin")
        url = reverse("reviews:update_review_json", args=[r.id])
        res = self.client.patch(url, data='{"rating":4}', content_type="application/json")
        self.assertEqual(res.status_code, 200)

    # ------- DELETE -------
    def test_delete_by_owner(self):
        r = self.create_review(self.user, rating=4)
        self.login("user")
        url = reverse("reviews:delete_review_json", args=[r.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Review.objects.filter(pk=r.id).exists())

    def test_delete_forbidden_if_not_owner(self):
        r = self.create_review(self.user, rating=4)
        self.login("other")
        url = reverse("reviews:delete_review_json", args=[r.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 403)

    def test_delete_by_admin_allowed(self):
        r = self.create_review(self.user, rating=4)
        self.login("admin")
        url = reverse("reviews:delete_review_json", args=[r.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 200)
