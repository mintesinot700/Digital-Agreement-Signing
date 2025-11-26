# Accounts/urls.py 

from django.urls import path
from .views import User_Register, UserListView, UserDeleteView,LogoutView , AdminVerificationView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [ 
    path('user/register/', User_Register.as_view(), name='register'),
    path('UserListView/', UserListView.as_view(), name='UserListView'),
    path('users/<int:pk>/', UserDeleteView.as_view(), name='user-delete'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('user/logout/', LogoutView.as_view(), name='logout'),    
    path('verify-admin/', AdminVerificationView.as_view(), name='verify-admin'),
]



