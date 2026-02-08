from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile, Follow

class UserModelTest(TestCase):
    def test_profile_created_on_user_creation(self):
        """Test that a Profile is automatically created when a User is created."""
        user = User.objects.create_user(username='testuser', password='password123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)
        self.assertEqual(str(user.profile), 'testuser Profile')

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_profile_access_authenticated(self):
        self.client.login(username='testuser', password='password123')
        # profile redirects to public_profile
        response = self.client.get(reverse('profile')) 
        self.assertEqual(response.status_code, 302) 

    def test_public_profile_view(self):
        response = self.client.get(reverse('public_profile', args=['testuser']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

    def test_follow_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('follow_user', args=['otheruser']))
        # Should redirect back to profile
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(Follow.objects.filter(user=self.user, following=self.other_user).exists())

    def test_unfollow_user(self):
        self.client.login(username='testuser', password='password123')
        Follow.objects.create(user=self.user, following=self.other_user)
        response = self.client.get(reverse('unfollow_user', args=['otheruser']))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Follow.objects.filter(user=self.user, following=self.other_user).exists())
