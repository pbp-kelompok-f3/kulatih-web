from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Coach, Member
from users.forms import CoachRegistrationForm, MemberRegistrationForm
from decimal import Decimal
import json


class CoachModelTest(TestCase):
    """Test cases for Coach model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testcoach',
            email='coach@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.coach = Coach.objects.create(
            user=self.user,
            sport='basketball',
            hourly_fee=Decimal('150000'),
            city='Jakarta',
            description='Experienced basketball coach',
            phone='08123456789'
        )
    
    def test_coach_creation(self):
        """Test coach object is created correctly"""
        self.assertEqual(self.coach.user.username, 'testcoach')
        self.assertEqual(self.coach.sport, 'basketball')
        self.assertEqual(self.coach.hourly_fee, Decimal('150000'))
        self.assertEqual(self.coach.city, 'Jakarta')
    
    def test_coach_str(self):
        """Test coach string representation"""
        self.assertEqual(str(self.coach), 'testcoach')
    
    def test_get_sport_display(self):
        """Test sport display method"""
        self.assertEqual(self.coach.get_sport_display(), 'Basketball')


class MemberModelTest(TestCase):
    """Test cases for Member model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testmember',
            email='member@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        self.member = Member.objects.create(
            user=self.user,
            city='Bandung',
            description='Fitness enthusiast',
            phone='08198765432'
        )
    
    def test_member_creation(self):
        """Test member object is created correctly"""
        self.assertEqual(self.member.user.username, 'testmember')
        self.assertEqual(self.member.city, 'Bandung')
        self.assertIsNotNone(self.member.description)
    
    def test_member_str(self):
        """Test member string representation"""
        self.assertEqual(str(self.member), 'testmember')


class CoachRegistrationFormTest(TestCase):
    """Test cases for Coach Registration Form"""
    
    def test_valid_coach_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'newcoach',
            'email': 'newcoach@test.com',
            'first_name': 'New',
            'last_name': 'Coach',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'sport': 'football',
            'hourly_fee': '200000',
            'city': 'Surabaya',
            'description': 'Professional football coach',
            'phone': '08111222333'
        }
        form = CoachRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_password_mismatch(self):
        """Test form with mismatched passwords"""
        form_data = {
            'username': 'newcoach',
            'email': 'newcoach@test.com',
            'first_name': 'New',
            'last_name': 'Coach',
            'password': 'securepass123',
            'confirm_password': 'differentpass123',
            'sport': 'football',
            'hourly_fee': '200000',
            'city': 'Surabaya'
        }
        form = CoachRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_duplicate_username(self):
        """Test form with existing username"""
        User.objects.create_user(username='existinguser', password='pass123')
        form_data = {
            'username': 'existinguser',
            'email': 'new@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'pass123',
            'confirm_password': 'pass123',
            'sport': 'tennis',
            'hourly_fee': '150000',
            'city': 'Jakarta'
        }
        form = CoachRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class MemberRegistrationFormTest(TestCase):
    """Test cases for Member Registration Form"""
    
    def test_valid_member_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'newmember',
            'email': 'newmember@test.com',
            'first_name': 'New',
            'last_name': 'Member',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'city': 'Yogyakarta',
            'description': 'Fitness enthusiast',
            'phone': '08555666777'
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_email(self):
        """Test form with invalid email"""
        form_data = {
            'username': 'newmember',
            'email': 'invalidemail',
            'first_name': 'New',
            'last_name': 'Member',
            'password': 'pass123',
            'confirm_password': 'pass123',
            'city': 'Jakarta'
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class LoginViewTest(TestCase):
    """Test cases for login view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.login_url = reverse('users:login')
    
    def test_login_page_loads(self):
        """Test login page loads successfully"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_successful_login(self):
        """Test successful login redirects"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')


class RegisterCoachViewTest(TestCase):
    """Test cases for coach registration view"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register_coach')
    
    def test_register_coach_page_loads(self):
        """Test registration page loads"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register_coach.html')
    
    def test_successful_coach_registration(self):
        """Test successful coach registration"""
        response = self.client.post(self.register_url, {
            'username': 'newcoach',
            'email': 'newcoach@test.com',
            'first_name': 'New',
            'last_name': 'Coach',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'sport': 'basketball',
            'hourly_fee': '200000',
            'city': 'Jakarta',
            'description': 'Pro coach',
            'phone': '08123456789'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newcoach').exists())
        self.assertTrue(Coach.objects.filter(user__username='newcoach').exists())


class RegisterMemberViewTest(TestCase):
    """Test cases for member registration view"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register_member')
    
    def test_register_member_page_loads(self):
        """Test registration page loads"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register_member.html')
    
    def test_successful_member_registration(self):
        """Test successful member registration"""
        response = self.client.post(self.register_url, {
            'username': 'newmember',
            'email': 'newmember@test.com',
            'first_name': 'New',
            'last_name': 'Member',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'city': 'Bandung',
            'description': 'Fitness lover',
            'phone': '08198765432'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newmember').exists())
        self.assertTrue(Member.objects.filter(user__username='newmember').exists())


class LogoutViewTest(TestCase):
    """Test cases for logout view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.logout_url = reverse('users:logout')
    
    def test_logout_redirects(self):
        """Test logout redirects to main page"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)


class CoachListViewTest(TestCase):
    """Test cases for coach list view"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('users:coach_list')
        
        # Create test coaches
        for i in range(3):
            user = User.objects.create_user(
                username=f'coach{i}',
                email=f'coach{i}@test.com',
                password='pass123',
                first_name=f'Coach{i}',
                last_name='Test'
            )
            Coach.objects.create(
                user=user,
                sport='basketball',
                hourly_fee=Decimal('150000'),
                city='Jakarta'
            )
    
    def test_coach_list_page_loads(self):
        """Test coach list page loads successfully"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coach_list.html')
    
    def test_coach_list_displays_coaches(self):
        """Test coach list displays all coaches"""
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['coaches']), 3)
    
    def test_coach_search(self):
        """Test coach search functionality"""
        response = self.client.get(self.url, {'q': 'coach0'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'coach0')
    
    def test_coach_filter_by_sport(self):
        """Test filtering coaches by sport"""
        response = self.client.get(self.url, {'sport': 'basketball'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['coaches']), 3)


class CoachDetailViewTest(TestCase):
    """Test cases for coach detail view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='detailcoach',
            email='detail@test.com',
            password='pass123',
            first_name='Detail',
            last_name='Coach'
        )
        self.coach = Coach.objects.create(
            user=self.user,
            sport='football',
            hourly_fee=Decimal('200000'),
            city='Jakarta',
            description='Experienced coach'
        )
        self.url = reverse('users:coach_detail', args=[self.coach.id])
    
    def test_coach_detail_page_loads(self):
        """Test coach detail page loads"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coach_detail.html')
    
    def test_coach_detail_displays_info(self):
        """Test coach detail displays correct information"""
        response = self.client.get(self.url)
        self.assertContains(response, 'Detail Coach')
        self.assertContains(response, 'Football')
        self.assertContains(response, '200000')


class ProfileViewTest(TestCase):
    """Test cases for profile views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create coach user
        self.coach_user = User.objects.create_user(
            username='coachuser',
            password='pass123',
            first_name='Coach',
            last_name='User'
        )
        self.coach = Coach.objects.create(
            user=self.coach_user,
            sport='tennis',
            hourly_fee=Decimal('150000'),
            city='Jakarta'
        )
        
        # Create member user
        self.member_user = User.objects.create_user(
            username='memberuser',
            password='pass123',
            first_name='Member',
            last_name='User'
        )
        self.member = Member.objects.create(
            user=self.member_user,
            city='Bandung'
        )
    
    def test_coach_profile_view(self):
        """Test coach profile page loads"""
        self.client.login(username='coachuser', password='pass123')
        response = self.client.get(reverse('users:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_coach.html')
    
    def test_member_profile_view(self):
        """Test member profile page loads"""
        self.client.login(username='memberuser', password='pass123')
        response = self.client.get(reverse('users:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_member.html')
    
    def test_unauthenticated_profile_redirect(self):
        """Test unauthenticated user redirects"""
        response = self.client.get(reverse('users:show_profile'))
        self.assertEqual(response.status_code, 302)


class EditProfileTest(TestCase):
    """Test cases for edit profile functionality"""
    
    def setUp(self):
        self.client = Client()
        self.coach_user = User.objects.create_user(
            username='editcoach',
            password='pass123'
        )
        self.coach = Coach.objects.create(
            user=self.coach_user,
            sport='basketball',
            hourly_fee=Decimal('150000'),
            city='Jakarta'
        )
    
    def test_edit_coach_profile(self):
        """Test editing coach profile"""
        self.client.login(username='editcoach', password='pass123')
        response = self.client.post(reverse('users:update_coach'), {
            'description': 'Updated description',
            'city': 'Bandung',
            'phone': '08123456789',
            'hourly_fee': '200000'
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify changes
        self.coach.refresh_from_db()
        self.assertEqual(self.coach.description, 'Updated description')
        self.assertEqual(self.coach.city, 'Bandung')


class GetCoachJSONTest(TestCase):
    """Test cases for JSON API endpoints"""
    
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(
            username='jsoncoach',
            password='pass123',
            first_name='JSON',
            last_name='Coach'
        )
        self.coach = Coach.objects.create(
            user=user,
            sport='swimming',
            hourly_fee=Decimal('180000'),
            city='Bali'
        )
    
    def test_get_coach_json(self):
        """Test getting coach data as JSON"""
        response = self.client.get(reverse('users:get_coach_json', args=[self.coach.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['username'], 'jsoncoach')
        self.assertEqual(data['sport'], 'swimming')