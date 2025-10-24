from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import IntegrityError 
from .models import Community, Membership, Message
from .forms import CommunityCreateForm, MessageForm
from . import views
import json


class CommunityModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.community = Community.objects.create(
            name="Test Community",
            short_description="Short desc",
            full_description="Full desc",
            created_by=self.user,
            profile_image_url="https://example.com/image.jpg"
        )

    def test_community_str_method(self):
        self.assertEqual(str(self.community), "Test Community")

    def test_community_members_count(self):
        """Test members_count method"""
        self.assertEqual(self.community.members_count(), 0)
        Membership.objects.create(community=self.community, user=self.user)
        self.assertEqual(self.community.members_count(), 1)
        Membership.objects.create(community=self.community, user=self.user2)
        self.assertEqual(self.community.members_count(), 2)

    def test_community_name_unique(self):
        """Test unique constraint on community name"""
        with self.assertRaises(IntegrityError):
            Community.objects.create(
                name="Test Community",  # Nama yang sama
                short_description="Another desc",
                full_description="Another full desc",
                created_by=self.user,
            )

    def test_membership_creation(self):
        member = Membership.objects.create(community=self.community, user=self.user)
        self.assertEqual(member.community.name, "Test Community")
        self.assertEqual(member.role, 'user')

    def test_membership_str_method(self):
        """Test Membership __str__ method"""
        member = Membership.objects.create(
            community=self.community,
            user=self.user,
            role='admin'
        )
        expected = f'{self.user} in {self.community} (admin)'
        self.assertEqual(str(member), expected)

    def test_membership_unique_constraint(self):
        """Test that user can't join same community twice"""
        Membership.objects.create(community=self.community, user=self.user)
        with self.assertRaises(Exception):
            Membership.objects.create(community=self.community, user=self.user)

    def test_message_creation(self):
        msg = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Hello World"
        )
        self.assertEqual(msg.text, "Hello World")
        self.assertEqual(msg.community, self.community)
        self.assertEqual(msg.sender, self.user)

    def test_message_str_method(self):
        """Test Message __str__ method with truncation"""
        long_text = "A" * 50
        msg = Message.objects.create(
            community=self.community,
            sender=self.user,
            text=long_text
        )
        self.assertEqual(str(msg), f'{self.user} @ {self.community}: {long_text[:30]}')

    def test_message_ordering(self):
        """Test messages are ordered by created_at"""
        msg1 = Message.objects.create(community=self.community, sender=self.user, text="First")
        msg2 = Message.objects.create(community=self.community, sender=self.user, text="Second")
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)


class CommunityFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")

    def test_valid_form_with_http_url(self):
        form_data = {
            'name': 'Valid Community',
            'short_description': 'Short desc',
            'full_description': 'Full description here',
            'profile_image_url': 'https://example.com/image.jpg'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_form_with_http_url_no_s(self):
        """Test HTTP (non-secure) URL is accepted"""
        form_data = {
            'name': 'Valid',
            'short_description': 'Short',
            'full_description': 'Full',
            'profile_image_url': 'http://example.com/image.jpg'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_form_with_base64_image(self):
        """Test data:image/ base64 URL is accepted"""
        form_data = {
            'name': 'Base64 Community',
            'short_description': 'Short',
            'full_description': 'Full',
            'profile_image_url': 'data:image/png;base64,iVBORw0KGgoAAAANS'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_form_without_image_url(self):
        """Test form is valid without profile image"""
        form_data = {
            'name': 'No Image Community',
            'short_description': 'Short',
            'full_description': 'Full',
            'profile_image_url': ''
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_empty_name(self):
        form_data = {
            'name': '',
            'short_description': 'Short',
            'full_description': 'Full'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn("Nama tidak boleh kosong.", form.errors['name'])

    def test_invalid_form_whitespace_only_name(self):
        """Test name with only whitespace is invalid"""
        form_data = {
            'name': '     ',
            'short_description': 'Short',
            'full_description': 'Full'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn("Nama tidak boleh kosong.", form.errors['name'])

    def test_invalid_profile_image_url(self):
        """Test invalid URL format is rejected"""
        form_data = {
            'name': 'Test',
            'short_description': 'Short',
            'full_description': 'Full',
            'profile_image_url': 'invalid-url-format'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('profile_image_url', form.errors)
        self.assertIn("URL harus dimulai dengan", form.errors['profile_image_url'][0])

    def test_form_save_with_user(self):
        """Test form save method assigns user correctly"""
        form_data = {
            'name': 'Save Test',
            'short_description': 'Short',
            'full_description': 'Full'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        community = form.save(user=self.user)
        self.assertEqual(community.created_by, self.user)

    def test_form_save_without_commit(self):
        """Test form save with commit=False"""
        form_data = {
            'name': 'No Commit',
            'short_description': 'Short',
            'full_description': 'Full'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        community = form.save(commit=False, user=self.user)
        self.assertIsNone(community.pk)

    def test_form_save_without_user(self):
        """Test form save without user raises IntegrityError"""
        form_data = {
            'name': 'No User Save',
            'short_description': 'Short',
            'full_description': 'Full'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Akan error karena created_by (user) tidak boleh NULL
        with self.assertRaises(IntegrityError):
            form.save()
    

    def test_message_form_valid(self):
        form_data = {'text': 'Hello everyone!'}
        form = MessageForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_message_form_empty(self):
        """Test message form with empty text"""
        form_data = {'text': ''}
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())


class CommunityViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="pew", password="12345")
        self.user2 = User.objects.create_user(username="user2", password="12345")
        self.community = Community.objects.create(
            name="Silat",
            short_description="Latihan bareng",
            full_description="Deskripsi lengkap",
            created_by=self.user
        )

    def test_community_home_authenticated(self):
        """Test home page for authenticated user"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/main_community.html')

    def test_community_home_unauthenticated(self):
        """Test home page for unauthenticated user"""
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/main_community.html')

    def test_community_home_search(self):
        """Test search functionality"""
        Community.objects.create(
            name="Basketball Club",
            short_description="Play basketball",
            full_description="We play basketball every week",
            created_by=self.user
        )
        response = self.client.get(reverse('community:home'), {'q': 'basketball'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Basketball Club')
        self.assertNotContains(response, 'Silat')

    def test_community_home_hides_joined_communities(self):
        """Test that joined communities are hidden from main page"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.community.name)

    def test_community_home_search_by_description(self):
        """Test search functionality by short_description"""
        response = self.client.get(reverse('community:home'), {'q': 'Latihan bareng'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Silat')

    def test_community_home_search_whitespace(self):
        """Test search with only whitespace query"""
        response = self.client.get(reverse('community:home'), {'q': '   '})
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, 'Silat')


    def test_community_home_authenticated_search(self):
        """Test search while authenticated (covers exclusion + query)"""
        self.client.login(username="pew", password="12345")
        community_joined = Community.objects.create(
            name="Joined", short_description="Test", full_description="Test", created_by=self.user
        )
        community_not_joined = Community.objects.create(
            name="Not Joined", short_description="Test", full_description="Test", created_by=self.user
        )
        Membership.objects.create(user=self.user, community=community_joined)
        
        response = self.client.get(reverse('community:home'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not Joined") # Harus muncul karena di-search
        self.assertNotContains(response, "Joined") # Tidak boleh muncul karena sudah join


    def test_community_detail_authenticated(self):
        """Test detail page for authenticated user"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:detail', args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.community.name)
        self.assertIn('is_member', response.context)
        self.assertFalse(response.context['is_member']) # Pastikan false jika belum join

    def test_community_detail_unauthenticated(self):
        """Test detail page for unauthenticated user"""
        response = self.client.get(reverse('community:detail', args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_member'])

    def test_community_detail_404(self):
        """Test detail page with invalid ID"""
        response = self.client.get(reverse('community:detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_community_detail_is_member(self):
        """Test detail page for a user who is a member"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.get(reverse('community:detail', args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_member'])

    def test_community_create_get(self):
        """Test GET request to create page"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:create'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CommunityCreateForm)

    def test_community_create_valid_post(self):
        """Test creating community with valid data"""
        self.client.login(username="pew", password="12345")
        response = self.client.post(reverse('community:create'), {
            'name': 'Basketball',
            'short_description': 'Play basketball',
            'full_description': 'Full Description here',
            'profile_image_url': 'https://example.com/image.png'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Community.objects.filter(name='Basketball').exists())
        
        community = Community.objects.get(name='Basketball')
        membership = Membership.objects.get(user=self.user, community=community)
        self.assertEqual(membership.role, 'admin')

    def test_community_create_invalid_post(self):
        """Test creating community with invalid data"""
        self.client.login(username="pew", password="12345")
        response = self.client.post(reverse('community:create'), {
            'name': '',
            'short_description': '',
            'full_description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Community.objects.filter(name='').exists())


    def test_community_create_post_duplicate_name(self):
        """Test creating community with duplicate name (triggers try-except)"""
        self.client.login(username="pew", password="12345")
        response = self.client.post(reverse('community:create'), {
            'name': 'Silat', # Nama duplikat
            'short_description': 'Short',
            'full_description': 'Full'
        })
        self.assertEqual(response.status_code, 200) # Harus render ulang form
        self.assertContains(response, 'Error:') # Cek pesan error dari exception
        self.assertEqual(Community.objects.filter(name='Silat').count(), 1) # Pastikan tidak ada duplikat
  

    def test_community_create_requires_login(self):
        """Test that create requires authentication"""
        response = self.client.get(reverse('community:create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_join_community_new_member(self):
        """Test joining a community for the first time"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:join', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Membership.objects.filter(user=self.user, community=self.community).exists())
        membership = Membership.objects.get(user=self.user, community=self.community)
        self.assertEqual(membership.role, 'user')

    def test_join_community_already_member(self):
        """Test joining a community that user is already a member of"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.get(reverse('community:join', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Membership.objects.filter(user=self.user, community=self.community).count(), 1)

    def test_join_community_requires_login(self):
        """Test that join requires authentication"""
        response = self.client.get(reverse('community:join', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_join_community_404(self):
        """Test joining a non-existent community"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:join', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_leave_community(self):
        """Test leaving a community"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.get(reverse('community:leave', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Membership.objects.filter(user=self.user, community=self.community).exists())

    def test_leave_community_requires_login(self):
        """Test that leave requires authentication"""
        response = self.client.get(reverse('community:leave', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_leave_community_404(self):
        """Test leaving a non-existent community"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:leave', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_leave_community_not_member(self):
        """Test leaving a community user is not a member of"""
        self.client.login(username="pew", password="12345")
        self.assertFalse(Membership.objects.filter(user=self.user, community=self.community).exists())
        response = self.client.get(reverse('community:leave', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Membership.objects.filter(user=self.user, community=self.community).exists()) 

    def test_my_community_list(self):
        """Test my community list page"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.get(reverse('community:my_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/my_list.html')
        self.assertIn('memberships', response.context)

    def test_my_community_list_requires_login(self):
        """Test that my list requires authentication"""
        response = self.client.get(reverse('community:my_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_my_community_list_empty(self):
        """Test my community list page when user has joined no communities"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:my_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/my_list.html')
        self.assertQuerysetEqual(response.context['memberships'], [])
        self.assertContains(response, "You haven’t joined any communities yet.")

    def test_my_community_group_get(self):
        """Test GET request to group chat"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.get(reverse('community:my_group', args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/group.html')

    def test_my_community_group_post_message(self):
        """Test posting message via form (non-AJAX)"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.post(
            reverse('community:my_group', args=[self.community.id]),
            {'text': 'Test message'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Message.objects.filter(text='Test message').exists())

    def test_my_community_group_post_invalid_message(self):
        """Test posting an empty message via form (non-AJAX)"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        response = self.client.post(
            reverse('community:my_group', args=[self.community.id]),
            {'text': ''} # Invalid empty message
        )
        self.assertEqual(response.status_code, 200) 
        self.assertFalse(Message.objects.filter(text='').exists())
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())

    def test_my_community_group_non_member(self):
        """Test that non-members can't access group chat"""
        self.client.login(username="pew", password="12345")
        response = self.client.get(reverse('community:my_group', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('community:detail', args=[self.community.id]))

    def test_my_community_group_requires_login(self):
        """Test that group requires authentication"""
        response = self.client.get(reverse('community:my_group', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_send_message_ajax_valid(self):
        """Test sending message via AJAX"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        url = reverse('community:send_message_ajax', args=[self.community.id])
        data = {'text': 'Hello AJAX'}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['text'], 'Hello AJAX')
        self.assertEqual(json_response['sender'], 'pew')
        self.assertEqual(json_response['community_id'], self.community.id)

    def test_send_message_ajax_empty_text(self):
        """Test sending empty message via AJAX"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        url = reverse('community:send_message_ajax', args=[self.community.id])
        data = {'text': '     '}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_send_message_ajax_get_request(self):
        """Test GET request to send_message_ajax returns error"""
        self.client.login(username="pew", password="12345")
        url = reverse('community:send_message_ajax', args=[self.community.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_send_message_ajax_requires_login(self):
        """Test that send message AJAX requires authentication"""
        url = reverse('community:send_message_ajax', args=[self.community.id])
        response = self.client.post(url, data=json.dumps({'text': 'test'}), content_type='application/json')
        self.assertEqual(response.status_code, 302)

    def test_send_message_ajax_invalid_community_404(self):
        """Test sending AJAX message to a non-existent community"""
        self.client.login(username="pew", password="12345")
        url = reverse('community:send_message_ajax', args=[9999])
        data = {'text': 'Hello AJAX'}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_send_message_ajax_non_member(self):
        """Test sending AJAX message as a logged-in non-member"""
        # Menggunakan user2 yang login tapi bukan member
        self.client.login(username="user2", password="12345") 
        url = reverse('community:send_message_ajax', args=[self.community.id])
        data = {'text': 'I am not a member'}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['text'], 'I am not a member')
        self.assertTrue(Message.objects.filter(text='I am not a member', sender=self.user2).exists())

    def test_edit_message_get(self):
        """Test GET request to edit message"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        msg = Message.objects.create(community=self.community, sender=self.user, text="Original")
        url = reverse('community:edit_message', args=[self.community.id, msg.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/edit_message.html')

    def test_edit_message_post(self):
        """Test POST request to edit message"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        msg = Message.objects.create(community=self.community, sender=self.user, text="Original")
        url = reverse('community:edit_message', args=[self.community.id, msg.id])
        response = self.client.post(url, {'text': 'Updated message'})
        self.assertEqual(response.status_code, 302)
        msg.refresh_from_db()
        self.assertEqual(msg.text, 'Updated message')

    def test_edit_message_wrong_user(self):
        """Test that users can't edit other users' messages"""
        self.client.login(username="user2", password="12345")
        msg = Message.objects.create(community=self.community, sender=self.user, text="Original")
        url = reverse('community:edit_message', args=[self.community.id, msg.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_message_requires_login(self):
        """Test that edit message requires authentication"""
        msg = Message.objects.create(community=self.community, sender=self.user, text="Original")
        url = reverse('community:edit_message', args=[self.community.id, msg.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_edit_message_post_invalid(self):
        """Test POST request to edit message with invalid data (empty)"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        msg = Message.objects.create(community=self.community, sender=self.user, text="Original")
        url = reverse('community:edit_message', args=[self.community.id, msg.id])
        response = self.client.post(url, {'text': ''}) # Teks kosong
        self.assertEqual(response.status_code, 200) # Harusnya render ulang form
        self.assertTemplateUsed(response, 'community/edit_message.html')
        self.assertFalse(response.context['form'].is_valid())
        msg.refresh_from_db()
        self.assertEqual(msg.text, 'Original') 

    def test_delete_message_ajax(self):
        """Test deleting message via AJAX"""
        self.client.login(username="pew", password="12345")
        Membership.objects.create(user=self.user, community=self.community)
        msg = Message.objects.create(community=self.community, sender=self.user, text="Delete me")
        url = reverse('community:delete_message', args=[self.community.id, msg.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.filter(id=msg.id).exists())

    def test_delete_message_wrong_user(self):
        """Test that users can't delete other users' messages"""
        self.client.login(username="user2", password="12345")
        msg = Message.objects.create(community=self.community, sender=self.user, text="Delete me")
        url = reverse('community:delete_message', args=[self.community.id, msg.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_message_post_request(self):
        """Test POST request to delete returns error"""
        self.client.login(username="pew", password="12345")
        msg = Message.objects.create(community=self.community, sender=self.user, text="Delete me")
        url = reverse('community:delete_message', args=[self.community.id, msg.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_delete_message_requires_login(self):
        """Test that delete message requires authentication"""
        msg = Message.objects.create(community=self.community, sender=self.user, text="Delete me")
        url = reverse('community:delete_message', args=[self.community.id, msg.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)


class CommunityURLTest(TestCase):
    def test_urls_resolve_correctly(self):
        """Test URL routing"""
        self.assertEqual(resolve('/community/').func, views.community_home)
        self.assertEqual(resolve('/community/create/').func, views.community_create)
        self.assertEqual(resolve('/community/1/').func, views.community_detail)
        self.assertEqual(resolve('/community/join/1/').func, views.join_community)
        self.assertEqual(resolve('/community/leave/1/').func, views.leave_community)
        self.assertEqual(resolve('/community/my/').func, views.my_community_list)
        self.assertEqual(resolve('/community/my/1/').func, views.my_community_group)
        self.assertEqual(resolve('/community/my/1/send_message_ajax/').func, views.send_message_ajax)
        self.assertEqual(resolve('/community/my/1/message/1/edit/').func, views.edit_message)
        self.assertEqual(resolve('/community/my/1/message/1/delete/').func, views.delete_message)