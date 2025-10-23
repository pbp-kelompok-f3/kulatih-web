from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import ForumPost


class ForumTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='12345')
        self.admin = User.objects.create_user(username='admin', password='admin123', is_staff=True)
        self.post = ForumPost.objects.create(author=self.user, content='Isi posting pertama')

    # Model Tests
    def test_post_str(self):
        self.assertIn(self.user.username, str(self.post))

    def test_like_post_method(self):
        initial_likes = self.post.likes
        self.post.like_post()
        self.assertEqual(self.post.likes, initial_likes + 1)

    def test_unlike_post_method(self):
        self.post.likes = 1
        self.post.save()
        self.post.unlike_post()
        self.assertEqual(self.post.likes, 0)

    def test_unlike_post_method_when_zero(self):
        """Pastikan unlike_post tidak error saat 0 likes"""
        self.post.likes = 0
        self.post.unlike_post()
        self.assertEqual(self.post.likes, 0)

    # View Tests
    def test_post_list_view_status(self):
        response = self.client.get(reverse('forum:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/post_list.html')

    def test_create_post_requires_login(self):
        response = self.client.get(reverse('forum:create_post'))
        self.assertEqual(response.status_code, 302)  # redirect ke login

    def test_create_post_success(self):
        self.client.login(username='tester', password='12345')
        response = self.client.post(reverse('forum:create_post'), {'content': 'Posting baru'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ForumPost.objects.filter(content='Posting baru').exists())

    def test_create_post_empty_content(self):
        """Pastikan post kosong tidak bisa dibuat"""
        self.client.login(username='tester', password='12345')
        response = self.client.post(reverse('forum:create_post'), {'content': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ForumPost.objects.count(), 1)  # masih 1 karena gagal tambah

    def test_like_post_view(self):
        self.client.login(username='tester', password='12345')
        response = self.client.get(reverse('forum:like_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 1)

    # Admin Custom Tests
    def test_admin_dashboard_requires_login(self):
        """Tanpa login -> redirect"""
        response = self.client.get(reverse('forum:admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_requires_staff(self):
        """User biasa tidak boleh akses dashboard"""
        self.client.login(username='tester', password='12345')
        response = self.client.get(reverse('forum:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # redirect karena bukan admin

    def test_admin_dashboard_access(self):
        """Admin bisa akses dashboard"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('forum:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/admin_dashboard.html')

    def test_delete_post_from_dashboard(self):
        """Admin bisa hapus posting"""
        self.client.login(username='admin', password='admin123')
        response = self.client.post(reverse('forum:delete_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ForumPost.objects.filter(id=self.post.id).exists())
