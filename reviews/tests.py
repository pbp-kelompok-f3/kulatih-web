# reviews/tests.py
import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Review

User = get_user_model()

class ReviewsApiTests(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(username="coach", password="x")
        self.user = User.objects.create_user(username="user", password="x")

    def test_list_empty(self):
        url = reverse("reviews:coach_reviews_json", args=[self.coach.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["stats"]["total"], 0)

    def test_create_once(self):
        self.client.login(username="user", password="x")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        body = json.dumps({"rating": 5, "comment": "mantap"})
        res = self.client.post(url, data=body, content_type="application/json")
        self.assertEqual(res.status_code, 201)
        # create lagi → harus gagal unique
        res2 = self.client.post(url, data=body, content_type="application/json")
        self.assertEqual(res2.status_code, 400)

    def test_cannot_review_self(self):
        self.client.login(username="coach", password="x")
        url = reverse("reviews:create_review_json", args=[self.coach.id])
        res = self.client.post(url, data=json.dumps({"rating": 4}), content_type="application/json")
        self.assertEqual(res.status_code, 403)
