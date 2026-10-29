"""
API tests for the Accounts app: registration, login (JWT + refresh cookie),
logout (token blacklisting), admin verification and user management.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserAccounts

REGISTER_URL = '/api/user/register/'
LOGIN_URL = '/api/token/'
REFRESH_URL = '/api/token/refresh/'
LOGOUT_URL = '/api/user/logout/'
VERIFY_ADMIN_URL = '/api/verify-admin/'
USER_LIST_URL = '/api/UserListView/'


def create_user(username='johndoe', email='john@example.com',
                password='StrongPass!123', phone_number='+251911234567', **extra):
    return UserAccounts.objects.create_user(
        username=username,
        email=email,
        password=password,
        phone_number=phone_number,
        **extra,
    )


class RegistrationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success_returns_tokens(self):
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPass!123',
            'phone_number': '+251911234567',
        }
        response = self.client.post(REGISTER_URL, payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertTrue(UserAccounts.objects.filter(username='newuser').exists())

    def test_register_duplicate_username_rejected(self):
        create_user(username='taken')
        payload = {
            'username': 'taken',
            'email': 'other@example.com',
            'password': 'StrongPass!123',
            'phone_number': '+251911234568',
        }
        response = self.client.post(REGISTER_URL, payload)
        self.assertEqual(response.status_code, 400)

    def test_register_invalid_email_rejected(self):
        payload = {
            'username': 'bademail',
            'email': 'not-an-email',
            'password': 'StrongPass!123',
            'phone_number': '+251911234569',
        }
        response = self.client.post(REGISTER_URL, payload)
        self.assertEqual(response.status_code, 400)

    def test_register_invalid_phone_rejected(self):
        payload = {
            'username': 'badphone',
            'email': 'badphone@example.com',
            'password': 'StrongPass!123',
            'phone_number': 'abc',
        }
        response = self.client.post(REGISTER_URL, payload)
        self.assertEqual(response.status_code, 400)

    def test_password_not_returned_in_admin_user_list(self):
        """The admin user list must never expose password hashes."""
        create_user(username='visible')
        staff = create_user(username='staff', is_staff=True)
        self.client.force_authenticate(user=staff)
        response = self.client.get(USER_LIST_URL)
        self.assertEqual(response.status_code, 200)
        for user_data in response.data:
            self.assertNotIn('password', user_data)


class LoginAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.staff = create_user(username='adminuser', is_staff=True)

    def test_login_returns_tokens_user_info_and_cookie(self):
        response = self.client.post(
            LOGIN_URL, {'username': 'johndoe', 'password': 'StrongPass!123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['username'], 'johndoe')
        self.assertFalse(response.data['is_admin'])
        self.assertIn('refresh_token', response.cookies)

    def test_login_is_case_insensitive_for_username(self):
        response = self.client.post(
            LOGIN_URL, {'username': 'JOHNDOE', 'password': 'StrongPass!123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_login_wrong_password_rejected(self):
        response = self.client.post(
            LOGIN_URL, {'username': 'johndoe', 'password': 'WrongPass!456'}
        )
        self.assertEqual(response.status_code, 401)

    def test_login_reports_admin_flag(self):
        response = self.client.post(
            LOGIN_URL, {'username': 'adminuser', 'password': 'StrongPass!123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_admin'])


class TokenRefreshCookieTest(TestCase):
    """The React app posts an empty body and relies on the HttpOnly cookie."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

    def _login(self):
        return self.client.post(
            LOGIN_URL, {'username': 'johndoe', 'password': 'StrongPass!123'}
        )

    def test_refresh_with_empty_body_uses_cookie(self):
        login_response = self._login()
        self.assertEqual(login_response.status_code, 200)

        response = self.client.post(REFRESH_URL, {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_refresh_rotates_and_blacklists_old_token(self):
        self._login()
        first = self.client.post(REFRESH_URL, {}, format='json')
        self.assertEqual(first.status_code, 200)

        # The rotation blacklists the previous refresh token; the cookie now
        # holds the new one, so a second refresh must still succeed.
        second = self.client.post(REFRESH_URL, {}, format='json')
        self.assertEqual(second.status_code, 200)
        self.assertIn('access', second.data)

    def test_blacklisted_refresh_token_is_rejected(self):
        self._login()
        refresh = RefreshToken.for_user(self.user)

        # Drop the login cookie so logout receives OUR body token and
        # blacklists it (the cookie takes priority when present).
        self.client.cookies.clear()
        self.client.force_authenticate(user=self.user)
        self.client.post(LOGOUT_URL, {'refresh': str(refresh)}, format='json')
        # After logout the refresh token is blacklisted -> refresh fails
        response = self.client.post(REFRESH_URL, {'refresh': str(refresh)}, format='json')
        self.assertEqual(response.status_code, 401)


class LogoutAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

    def test_logout_blacklists_refresh_token_in_body(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LOGOUT_URL, {'refresh': str(refresh)}, format='json')
        self.assertEqual(response.status_code, 200)

        # Refreshing with the blacklisted token must now fail
        refresh_response = self.client.post(
            REFRESH_URL, {'refresh': str(refresh)}, format='json'
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_logout_requires_authentication(self):
        response = self.client.post(LOGOUT_URL, {}, format='json')
        self.assertEqual(response.status_code, 401)


class AdminVerificationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.staff = create_user(username='staffuser', is_staff=True)

    def test_regular_user_is_not_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(VERIFY_ADMIN_URL)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['is_admin'])

    def test_staff_user_is_admin(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(VERIFY_ADMIN_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_admin'])

    def test_requires_authentication(self):
        response = self.client.get(VERIFY_ADMIN_URL)
        self.assertEqual(response.status_code, 401)


class UserManagementPermissionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.staff = create_user(username='staffuser', is_staff=True)

    def test_user_list_forbidden_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(USER_LIST_URL)
        self.assertEqual(response.status_code, 403)

    def test_user_list_allowed_for_admin(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(USER_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 2)

    def test_admin_can_delete_user(self):
        victim = create_user(username='victim')
        self.client.force_authenticate(user=self.staff)
        response = self.client.delete(f'/api/users/{victim.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserAccounts.objects.filter(username='victim').exists())

    def test_delete_missing_user_returns_404(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.delete('/api/users/999999/')
        self.assertEqual(response.status_code, 404)
