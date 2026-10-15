from django.test import TestCase
from django.urls import reverse

from utils.testing import REGISTER_DATA, make_user

from .models import User


class RegistrationTests(TestCase):
    def test_register_creates_user_with_address_and_hashed_password(self):
        response = self.client.post(reverse('account_register'), REGISTER_DATA)
        self.assertRedirects(response, reverse('home_page'))
        user = User.objects.get(email='ada@example.com')
        self.assertEqual(user.city, 'Test City')
        self.assertEqual(user.postal_code, '12345')
        self.assertNotEqual(user.password, REGISTER_DATA['password'])
        self.assertTrue(user.check_password(REGISTER_DATA['password']))
        self.assertIn('_auth_user_id', self.client.session)

    def test_duplicate_email_is_rejected(self):
        make_user('ada@example.com')
        response = self.client.post(reverse('account_register'), REGISTER_DATA)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')
        self.assertEqual(User.objects.filter(email__iexact='ada@example.com').count(), 1)

    def test_password_mismatch_is_rejected(self):
        data = dict(REGISTER_DATA, confirm_password='different')
        response = self.client.post(reverse('account_register'), data)
        self.assertContains(response, 'do not match')
        self.assertFalse(User.objects.filter(email='ada@example.com').exists())

    def test_address_fields_are_required(self):
        data = dict(REGISTER_DATA, city='')
        response = self.client.post(reverse('account_register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='ada@example.com').exists())


class LoginTests(TestCase):
    def setUp(self):
        self.user = make_user('buyer@example.com')

    def test_login_with_email(self):
        response = self.client.post(reverse('account_login'),
                                    {'email': 'BUYER@example.com', 'password': 'S3cure-pass-123'})
        self.assertRedirects(response, reverse('home_page'))

    def test_wrong_password(self):
        response = self.client.post(reverse('account_login'), {'email': 'buyer@example.com', 'password': 'nope'})
        self.assertContains(response, 'Incorrect email or password')

    def test_external_next_url_is_ignored(self):
        response = self.client.post(reverse('account_login'), {
            'email': 'buyer@example.com', 'password': 'S3cure-pass-123', 'next': 'https://evil.example.org/'})
        self.assertRedirects(response, reverse('home_page'))

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('account_logout')).status_code, 405)
        self.client.post(reverse('account_logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_account_page_requires_login(self):
        response = self.client.get(reverse('account_page'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('account_login'), response['Location'])

    def test_user_can_edit_address(self):
        self.client.force_login(self.user)
        data = {'form_type': 'address', 'country': 'A', 'state': 'B', 'city': 'C', 'street_address': 'D', 'postal_code': 'E'}
        self.client.post(reverse('account_page'), data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.city, 'C')
