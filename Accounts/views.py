from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .serializers import UserAccountsSerializers
from .models import UserAccounts
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


# User Registration
class User_Register(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserAccountsSerializers

    def post(self, request):
        serializer = UserAccountsSerializers(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Registration successful!',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View List of users by the Admin
class UserListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserAccountsSerializers

    def get_queryset(self):
        return UserAccounts.objects.all().order_by('id')


# User Login (kept for backwards compatibility; the React app uses /api/token/)
class User_Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''
        if not username or not password:
            return Response(
                {'error': 'Both username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Case-insensitive username lookup, then authenticate the exact user.
        user_obj = UserAccounts.objects.filter(username__iexact=username).first()
        user = None
        if user_obj:
            user = authenticate(username=user_obj.username, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({
            'access': access_token,
            'refresh': str(refresh),
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_staff,
        }, status=status.HTTP_200_OK)
        response.set_cookie(
            settings.REFRESH_COOKIE_NAME,
            str(refresh),
            max_age=settings.REFRESH_COOKIE_MAX_AGE,
            httponly=settings.REFRESH_COOKIE_HTTPONLY,
            secure=settings.REFRESH_COOKIE_SECURE,
            samesite=settings.REFRESH_COOKIE_SAMESITE,
            path='/',
        )
        return response


# Accounts/views.py
class UserDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            user = UserAccounts.objects.get(pk=pk)
            if user.is_superuser and not request.user.is_superuser:
                return Response(
                    {'detail': 'Only superusers can delete superuser accounts.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserAccounts.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Blacklist the refresh token (cookie or body) so it can no longer mint
        # new access tokens. Requires rest_framework_simplejwt.token_blacklist.
        refresh_token = (
            request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
            or request.data.get('refresh')
        )
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # token already expired/blacklisted — nothing to do

        response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.REFRESH_COOKIE_NAME, path='/')

        if hasattr(request, 'session'):
            request.session.flush()

        return response


# --- ADMIN VERIFICATION VIEW ---
class AdminVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        is_admin = request.user.is_staff or request.user.is_superuser
        return Response({'is_admin': is_admin}, status=status.HTTP_200_OK)
