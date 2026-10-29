# Accounts/urls.py

from django.urls import path
from .views import User_Register, UserListView, UserDeleteView, User_Login, LogoutView, AdminVerificationView
from .auth_views import LoginView, RefreshCookieView

urlpatterns = [
    path('user/register/', User_Register.as_view(), name='register'),
    path('user/login/', User_Login.as_view(), name='user-login'),
    path('UserListView/', UserListView.as_view(), name='UserListView'),
    path('users/<int:pk>/', UserDeleteView.as_view(), name='user-delete'),
    path('token/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', RefreshCookieView.as_view(), name='token_refresh'),
    path('user/logout/', LogoutView.as_view(), name='logout'),
    path('verify-admin/', AdminVerificationView.as_view(), name='verify-admin'),
]
