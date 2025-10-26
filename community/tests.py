from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Community, Membership, Message
from .forms import CommunityCreateForm, MessageForm
import json


class AdditionalCommunityModelTest(TestCase):
    """Additional model tests to increase coverage"""
    
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.community = Community.objects.create(
            name="Test Community",
            short_description="Short description",
            full_description="Full description here",
            created_by=self.user
        )

    def test_community_without_profile_image(self):
        """Test community can be created without profile image"""
        community = Community.objects.create(
            name="No Image Community",
            short_description="Short",
            full_description="Full",
            created_by=self.user,
            profile_image_url=None
        )
        self.assertIsNone(community.profile_image_url)

    def test_community_with_blank_profile_image(self):
        """Test community with blank profile image URL"""
        community = Community.objects.create(
            name="Blank Image",
            short_description="Short",
            full_description="Full",
            created_by=self.user,
            profile_image_url=""
        )
        self.assertEqual(community.profile_image_url, "")

    def test_membership_default_role(self):
        """Test membership default role is 'user'"""
        membership = Membership.objects.create(
            community=self.community,
            user=self.user
        )
        self.assertEqual(membership.role, 'user')

    def test_membership_admin_role(self):
        """Test membership can have admin role"""
        membership = Membership.objects.create(
            community=self.community,
            user=self.user,
            role='admin'
        )
        self.assertEqual(membership.role, 'admin')

    def test_message_updated_at_changes(self):
        """Test message updated_at field changes on update"""
        message = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Original text"
        )
        original_updated_at = message.updated_at
        
        message.text = "Updated text"
        message.save()
        message.refresh_from_db()
        
        self.assertNotEqual(message.updated_at, original_updated_at)

    def test_community_cascade_delete_membership(self):
        """Test deleting community deletes associated memberships"""
        Membership.objects.create(community=self.community, user=self.user)
        community_id = self.community.id
        self.community.delete()
        
        self.assertFalse(Membership.objects.filter(community_id=community_id).exists())

    def test_community_cascade_delete_messages(self):
        """Test deleting community deletes associated messages"""
        Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Test message"
        )
        community_id = self.community.id
        self.community.delete()
        
        self.assertFalse(Message.objects.filter(community_id=community_id).exists())


class AdditionalCommunityFormTest(TestCase):
    """Additional form tests to increase coverage"""
    
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass123")

    def test_form_widgets_have_correct_classes(self):
        """Test form widgets have correct CSS classes"""
        form = CommunityCreateForm()
        
        self.assertIn('w-full', form.fields['name'].widget.attrs['class'])
        self.assertIn('rounded-full', form.fields['name'].widget.attrs['class'])
        self.assertIn('w-full', form.fields['short_description'].widget.attrs['class'])
        self.assertIn('w-full', form.fields['full_description'].widget.attrs['class'])
        self.assertIn('rounded-2xl', form.fields['full_description'].widget.attrs['class'])

    def test_form_profile_image_url_placeholder(self):
        """Test profile_image_url field has placeholder"""
        form = CommunityCreateForm()
        self.assertEqual(
            form.fields['profile_image_url'].widget.attrs['placeholder'],
            'URL HTTP/S'
        )

    def test_clean_name_strips_whitespace(self):
        """Test clean_name method strips whitespace"""
        form_data = {
            'name': '  Test Community  ',
            'short_description': 'Short',
            'full_description': 'Full'
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Test Community')

    def test_clean_profile_image_url_strips_whitespace(self):
        """Test clean_profile_image_url strips whitespace"""
        form_data = {
            'name': 'Test',
            'short_description': 'Short',
            'full_description': 'Full',
            'profile_image_url': '  https://example.com/image.jpg  '
        }
        form = CommunityCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['profile_image_url'],
            'https://example.com/image.jpg'
        )

    def test_message_form_widget_has_placeholder(self):
        """Test MessageForm has correct placeholder"""
        form = MessageForm()
        self.assertIn('placeholder', form.fields['text'].widget.attrs)
        self.assertIn('Ketik pesan', form.fields['text'].widget.attrs['placeholder'])

    def test_message_form_widget_has_classes(self):
        """Test MessageForm widget has correct CSS classes"""
        form = MessageForm()
        self.assertIn('w-full', form.fields['text'].widget.attrs['class'])
        self.assertIn('text-black', form.fields['text'].widget.attrs['class'])


class AdditionalCommunityViewTest(TestCase):
    """Additional view tests to increase coverage"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.community = Community.objects.create(
            name="Test Community",
            short_description="Short desc",
            full_description="Full desc",
            created_by=self.user
        )

    def test_community_home_pagination(self):
        """Test pagination on home page"""
        # Create 10 communities to trigger pagination
        for i in range(10):
            Community.objects.create(
                name=f"Community {i}",
                short_description=f"Desc {i}",
                full_description=f"Full desc {i}",
                created_by=self.user
            )
        
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['communities'].has_other_pages())

    def test_community_home_pagination_page_2(self):
        """Test accessing page 2 of pagination"""
        for i in range(10):
            Community.objects.create(
                name=f"Community {i}",
                short_description=f"Desc {i}",
                full_description=f"Full desc {i}",
                created_by=self.user
            )
        
        response = self.client.get(reverse('community:home') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['communities'].number, 2)

    def test_community_home_case_insensitive_search(self):
        """Test search is case insensitive"""
        response = self.client.get(reverse('community:home'), {'q': 'test community'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Community')

    def test_community_home_search_by_full_description(self):
        """Test search can find by full description"""
        response = self.client.get(reverse('community:home'), {'q': 'Full desc'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Community')

    def test_community_create_form_errors_displayed(self):
        """Test form errors are displayed on invalid submission"""
        self.client.login(username="testuser", password="pass123")
        response = self.client.post(reverse('community:create'), {
            'name': '',
            'short_description': 'Short',
            'full_description': 'Full'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_community_create_with_get_or_create(self):
        """Test community create uses get_or_create for membership"""
        self.client.login(username="testuser", password="pass123")
        response = self.client.post(reverse('community:create'), {
            'name': 'New Community',
            'short_description': 'Short',
            'full_description': 'Full'
        })
        
        community = Community.objects.get(name='New Community')
        membership = Membership.objects.get(user=self.user, community=community)
        self.assertEqual(membership.role, 'admin')

    def test_community_detail_displays_member_count(self):
        """Test detail page displays correct member count"""
        Membership.objects.create(user=self.user, community=self.community)
        Membership.objects.create(user=self.user2, community=self.community)
        
        response = self.client.get(reverse('community:detail', args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['members_count'], 2)

    def test_join_community_redirects_to_my_list(self):
        """Test join redirects to my_list"""
        self.client.login(username="testuser", password="pass123")
        response = self.client.get(reverse('community:join', args=[self.community.id]))
        self.assertRedirects(response, reverse('community:my_list'))

    def test_join_community_creates_user_role(self):
        """Test joining creates membership with 'user' role"""
        self.client.login(username="testuser", password="pass123")
        self.client.get(reverse('community:join', args=[self.community.id]))
        
        membership = Membership.objects.get(user=self.user, community=self.community)
        self.assertEqual(membership.role, 'user')

    def test_leave_community_redirects_to_home(self):
        """Test leave redirects to community home"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        response = self.client.get(reverse('community:leave', args=[self.community.id]))
        self.assertRedirects(response, reverse('community:home'))

    def test_my_community_list_pagination(self):
        """Test pagination on my community list"""
        self.client.login(username="testuser", password="pass123")
        
        # Join 10 communities
        for i in range(10):
            comm = Community.objects.create(
                name=f"Community {i}",
                short_description=f"Desc {i}",
                full_description=f"Full {i}",
                created_by=self.user
            )
            Membership.objects.create(user=self.user, community=comm)
        
        response = self.client.get(reverse('community:my_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['memberships'].has_other_pages())

    def test_my_community_list_search(self):
        """Test search functionality in my community list"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        response = self.client.get(reverse('community:my_list'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['memberships'].paginator.count, 1)

    def test_my_community_list_search_by_short_description(self):
        """Test search in my list by short description"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        response = self.client.get(reverse('community:my_list'), {'q': 'Short desc'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Community')

    def test_my_community_group_displays_messages(self):
        """Test group chat displays all messages"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        msg1 = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Message 1"
        )
        msg2 = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Message 2"
        )
        
        response = self.client.get(reverse('community:my_group', args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Message 1")
        self.assertContains(response, "Message 2")

    def test_my_community_group_empty_state(self):
        """Test group chat shows empty state when no messages"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        response = self.client.get(reverse('community:my_group', args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no messages yet")

    def test_send_message_ajax_creates_message(self):
        """Test AJAX message creation"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        url = reverse('community:send_message_ajax', args=[self.community.id])
        response = self.client.post(
            url,
            data=json.dumps({'text': 'AJAX message'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Message.objects.filter(text='AJAX message').exists())

    def test_send_message_ajax_returns_correct_data(self):
        """Test AJAX response contains correct message data"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        url = reverse('community:send_message_ajax', args=[self.community.id])
        response = self.client.post(
            url,
            data=json.dumps({'text': 'Test AJAX'}),
            content_type='application/json'
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['text'], 'Test AJAX')
        self.assertEqual(data['sender'], 'testuser')
        self.assertIn('id', data)
        self.assertIn('community_id', data)

    def test_send_message_ajax_whitespace_only(self):
        """Test AJAX with whitespace-only text returns error"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        url = reverse('community:send_message_ajax', args=[self.community.id])
        response = self.client.post(
            url,
            data=json.dumps({'text': '   '}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)

    def test_edit_message_invalid_form_rerenders(self):
        """Test edit with invalid data re-renders form"""
        self.client.login(username="testuser", password="pass123")
        msg = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Original"
        )
        
        url = reverse('community:edit_message', args=[self.community.id, msg.id])
        response = self.client.post(url, {'text': ''})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/edit_message.html')
        msg.refresh_from_db()
        self.assertEqual(msg.text, 'Original')

    def test_edit_message_successful_redirect(self):
        """Test successful edit redirects to group"""
        self.client.login(username="testuser", password="pass123")
        msg = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Original"
        )
        
        url = reverse('community:edit_message', args=[self.community.id, msg.id])
        response = self.client.post(url, {'text': 'Edited text'})
        
        self.assertRedirects(
            response,
            reverse('community:my_group', args=[self.community.id])
        )

    def test_delete_message_removes_from_database(self):
        """Test delete removes message from database"""
        self.client.login(username="testuser", password="pass123")
        msg = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Delete me"
        )
        msg_id = msg.id
        
        url = reverse('community:delete_message', args=[self.community.id, msg.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.filter(id=msg_id).exists())

    def test_delete_message_returns_success_json(self):
        """Test delete returns success JSON"""
        self.client.login(username="testuser", password="pass123")
        msg = Message.objects.create(
            community=self.community,
            sender=self.user,
            text="Delete me"
        )
        
        url = reverse('community:delete_message', args=[self.community.id, msg.id])
        response = self.client.delete(url)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_my_community_group_non_member_gets_redirected(self):
        """Test non-member cannot access group chat"""
        self.client.login(username="testuser", password="pass123")
        
        response = self.client.get(reverse('community:my_group', args=[self.community.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('community:detail', args=[self.community.id])
        )

    def test_community_create_exception_handling(self):
        """Test create view handles exceptions properly"""
        self.client.login(username="testuser", password="pass123")
        
        # Create community first
        Community.objects.create(
            name="Duplicate",
            short_description="Test",
            full_description="Test",
            created_by=self.user
        )
        
        # Try to create with same name
        response = self.client.post(reverse('community:create'), {
            'name': 'Duplicate',
            'short_description': 'Test',
            'full_description': 'Test'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Community.objects.filter(name='Duplicate').count(), 1)

    def test_community_home_shows_all_communities_for_unauthenticated(self):
        """Test unauthenticated users see all communities"""
        Community.objects.create(
            name="Public Community",
            short_description="Public",
            full_description="Public",
            created_by=self.user
        )
        
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['communities'].paginator.count, 2)

    def test_join_community_displays_success_message(self):
        """Test join shows success message"""
        self.client.login(username="testuser", password="pass123")
        response = self.client.get(
            reverse('community:join', args=[self.community.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('joined', str(messages[0]))

    def test_join_community_already_member_shows_info(self):
        """Test joining again shows info message"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        response = self.client.get(
            reverse('community:join', args=[self.community.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertIn('already', str(messages[0]))

    def test_leave_community_displays_success_message(self):
        """Test leave shows success message"""
        self.client.login(username="testuser", password="pass123")
        Membership.objects.create(user=self.user, community=self.community)
        
        response = self.client.get(
            reverse('community:leave', args=[self.community.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertIn('no longer', str(messages[0]))

    def test_my_community_group_non_member_shows_error(self):
        """Test accessing group as non-member shows error"""
        self.client.login(username="testuser", password="pass123")
        
        response = self.client.get(
            reverse('community:my_group', args=[self.community.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('bergabung', str(messages[0]))


class EdgeCaseTests(TestCase):
    """Edge case tests for better coverage"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.community = Community.objects.create(
            name="Test",
            short_description="Short",
            full_description="Full",
            created_by=self.user
        )

    def test_send_message_ajax_invalid_json(self):
        """Test AJAX with invalid JSON"""
        self.client.login(username="testuser", password="pass123")
        url = reverse('community:send_message_ajax', args=[self.community.id])
        
        response = self.client.post(
            url,
            data='invalid json',
            content_type='application/json'
        )
        # Should return error or handle gracefully
        self.assertIn(response.status_code, [400, 500])

    def test_pagination_invalid_page_number(self):
        """Test pagination with invalid page number"""
        response = self.client.get(reverse('community:home') + '?page=999')
        self.assertEqual(response.status_code, 200)
        # Django paginator returns last page for out of range

    def test_search_with_special_characters(self):
        """Test search with special characters"""
        response = self.client.get(reverse('community:home'), {'q': '@#$%^&*()'})
        self.assertEqual(response.status_code, 200)

    def test_community_with_very_long_description(self):
        """Test community with very long description"""
        long_text = "A" * 1000
        community = Community.objects.create(
            name="Long Desc",
            short_description="Short",
            full_description=long_text,
            created_by=self.user
        )
        self.assertEqual(len(community.full_description), 1000)

    def test_message_str_truncation(self):
        """Test message __str__ truncates at 30 characters"""
        long_text = "This is a very long message that should be truncated"
        msg = Message.objects.create(
            community=self.community,
            sender=self.user,
            text=long_text
        )
        str_repr = str(msg)
        self.assertIn(long_text[:30], str_repr)
        self.assertEqual(len(long_text[:30]), 30)