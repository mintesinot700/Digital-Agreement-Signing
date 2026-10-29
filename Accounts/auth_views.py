"""
JWT authentication views with HttpOnly refresh-cookie support.

Why custom views?
- The React frontend posts an EMPTY body to /api/token/refresh/ and expects the
  refresh token to travel in an HttpOnly cookie (see src/api.js). The stock
  SimpleJWT views only read the request body, so token refresh never worked and
  users were logged out as soon as their access token expired.
- The stock login response contains only `access`/`refresh`; the frontend needs
  `user_id`, `username` and `is_admin` right away.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed


def _set_refresh_cookie(response, refresh_token: str) -> None:
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=settings.REFRESH_COOKIE_MAX_AGE,
        httponly=settings.REFRESH_COOKIE_HTTPONLY,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path='/',
    )


class UserInfoTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login serializer that also authenticates case-insensitively and
    returns basic user info alongside the tokens."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_admin'] = user.is_staff or user.is_superuser
        return token

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        from Accounts.models import UserAccounts

        username = (attrs.get(self.username_field) or '').strip()
        password = attrs.get('password') or ''

        # Case-insensitive username lookup, then authenticate the exact user.
        user_obj = UserAccounts.objects.filter(username__iexact=username).first()
        user = None
        if user_obj:
            user = authenticate(
                request=self.context.get('request'),
                username=user_obj.username,
                password=password,
            )
            if user is not None and not getattr(user, 'is_active', True):
                raise AuthenticationFailed('User account is disabled.', code='user_inactive')
        else:
            user = None

        if user is None:
            raise AuthenticationFailed(
                'No active account found with the given credentials',
                code='no_active_account',
            )

        self.user = user
        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'username': user.username,
            'is_admin': bool(user.is_staff or user.is_superuser),
        }
        return data


class LoginView(TokenObtainPairView):
    """POST /api/token/ — returns access token + user info, sets the refresh
    token as an HttpOnly cookie (it is still returned in the body for
    backwards compatibility)."""
    serializer_class = UserInfoTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK and response.data.get('refresh'):
            _set_refresh_cookie(response, response.data['refresh'])
        return response


class RefreshCookieView(TokenRefreshView):
    """POST /api/token/refresh/ — reads the refresh token from the HttpOnly
    cookie (or the request body as a fallback) and rotates it."""

    def post(self, request, *args, **kwargs):
        if not request.data.get('refresh'):
            cookie_refresh = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
            if cookie_refresh:
                request._full_data = {'refresh': cookie_refresh}
        response = super().post(request, *args, **kwargs)

        # Rotation: SimpleJWT returns a new refresh token when
        # ROTATE_REFRESH_TOKENS=True — store the new one in the cookie.
        if response.status_code == status.HTTP_200_OK and response.data.get('refresh'):
            _set_refresh_cookie(response, response.data['refresh'])
        return response
