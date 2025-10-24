# reviews/tests.py
import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import Coach, Member
from reviews.models import Review

User = get_user_model()


class ReviewsViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # users
        self.user_member = User.objects.create_user(
            username="member1", email="m1@example.com", password="pass12345"
        )
        self.user_other = User.objects.create_user(
            username="other", email="o@example.com", password="pass12345"
        )
        self.user_admin = User.objects.create_user(
            username="admin", email="a@example.com", password="pass12345", is_staff=True
        )

        # profiles
        self.member = Member.objects.create(user=self.user_member)
        self.other_member = Member.objects.create(user=self.user_other)

        # coaches (pk UUID)
        self.coach_user = User.objects.create_user(
            username="coachuser", email="c@example.com", password="pass12345"
        )
        self.coach = Coach.objects.create(id=uuid.uuid4(), user=self.coach_user)

        self.other_coach = Coach.objects.create(id=uuid.uuid4(), user=self.user_admin)

        # existing review from member -> coach
        self.review = Review.objects.create(
            coach=self.coach, reviewer=self.member, rating=4, comment="good", created_at=timezone.now()
        )

    # LIST (coach_reviews_json)
    def test_list_default_latest(self):
        # create older and newer to test ordering
        Review.objects.create(coach=self.coach, reviewer=self.other_member, rating=2, comment="meh")
        url = reverse("reviews:coach_reviews_json", args=[self.coach.id])
        res = self.client.get(url)  
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertGreaterEqual(len(data["items"]), 2)
        self.assertEqual(data["items"][0]["rating"], 2)

    def test_list_sort_highest_lowest(self):
        Review.objects.create(coach=self.coach, reviewer=self.other_member, rating=1, comment="bad")
        # highest
        url = reverse("reviews:coach_reviews_json", args=[self.coach.id])
        res = self.client.get(url, {"sort": "highest"})
        ratings = [it["rating"] for it in res.json()["items"]]
        self.assertEqual(ratings, sorted(ratings, reverse=True))
        # lowest
        res = self.client.get(url, {"sort": "lowest"})
        ratings = [it["rating"] for it in res.json()["items"]]
        self.assertEqual(ratings, sorted(ratings))

    def test_list_pagination(self):
        for i in range(15):
            u = User.objects.create_user(
                username=f"tmp{i}", email=f"t{i}@ex.com", password="x"
            )
            m = Member.objects.create(user=u)
            Review.objects.create(
                coach=self.coach, reviewer=m, rating=3, comment=str(i)
            )

        url = reverse("reviews:coach_reviews_json", args=[self.coach.id])
        res = self.client.get(url, {"page": 2, "page_size": 5})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["pagination"]["page_size"], 5)
        self.assertEqual(data["pagination"]["page"], 2)
        self.assertTrue(data["pagination"]["has_previous"])
        self.assertTrue(data["pagination"]["has_next"])

    # DETAIL JSON
    def test_review_detail_json(self):
        url = reverse("reviews:review_detail_json", args=[self.review.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], str(self.review.id))
        self.assertEqual(data["rating"], 4)
        self.assertIn("coach", data)
        self.assertIn("reviewer", data)

    # CREATE
    def test_create_requires_login(self):
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        res = self.client.post(url, data=json.dumps({"rating": 5}), content_type="application/json")
        # Django will redirect to login (302) or 302->200 for test client, accept 302
        self.assertIn(res.status_code, (302, 401, 403))

    def test_create_success(self):
        self.client.login(username="member1", password="pass12345")
        # create review for other_coach to avoid unique clash with existing
        url = reverse("reviews:create_review_json", args=[self.other_coach.id])
        res = self.client.post(url, data=json.dumps({"rating": 5, "comment": "great"}), content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["rating"], 5)
        self.assertEqual(data["comment"], "great")

    def test_create_forbidden_self_review(self):
        # login as coach user and try to review himself -> 403
        self.client.login(username="coachuser", password="pass12345")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        res = self.client.post(url, data=json.dumps({"rating": 5}), content_type="application/json")
        self.assertEqual(res.status_code, 403)

    def test_create_unique_per_member_coach(self):
        self.client.login(username="member1", password="pass12345")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        # already has self.review for (member, coach) -> should 400 with error
        res = self.client.post(url, data=json.dumps({"rating": 5}), content_type="application/json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.json())

    def test_create_validate_rating(self):
        self.client.login(username="member1", password="pass12345")
        url = reverse("reviews:create_review_json", args=[self.other_coach.id])
        res = self.client.post(url, data=json.dumps({"rating": 10}), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # UPDATE
    def test_update_owner_ok(self):
        self.client.login(username="member1", password="pass12345")
        url = reverse("reviews:update_review_json", args=[self.review.id])
        res = self.client.post(url, data=json.dumps({"rating": 5, "comment": "upd"}), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, "upd")

    def test_update_non_owner_forbidden(self):
        self.client.login(username="other", password="pass12345")
        url = reverse("reviews:update_review_json", args=[self.review.id])
        res = self.client.post(url, data=json.dumps({"rating": 1}), content_type="application/json")
        self.assertEqual(res.status_code, 403)

    def test_update_admin_ok(self):
        self.client.login(username="admin", password="pass12345")
        url = reverse("reviews:update_review_json", args=[self.review.id])
        res = self.client.post(url, data=json.dumps({"rating": 3}), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)

    def test_update_validate_rating_range(self):
        self.client.login(username="member1", password="pass12345")
        url = reverse("reviews:update_review_json", args=[self.review.id])
        res = self.client.post(url, data=json.dumps({"rating": 0}), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # DELETE
    def test_delete_owner_ok(self):
        self.client.login(username="member1", password="pass12345")
        url = reverse("reviews:delete_review_json", args=[self.review.id])
        res = self.client.post(url)  # you also accept DELETE, but POST is fine
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_non_owner_forbidden(self):
        self.client.login(username="other", password="pass12345")
        # recreate a review to delete
        r = Review.objects.create(coach=self.other_coach, reviewer=self.member, rating=3)
        url = reverse("reviews:delete_review_json", args=[r.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 403)
        self.assertTrue(Review.objects.filter(id=r.id).exists())

    # PAGE
    def test_review_detail_page_renders(self):
        url = reverse("reviews:review_detail_page", args=[self.review.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "RATING AND FEEDBACK")
        self.assertContains(res, str(self.review.rating))
