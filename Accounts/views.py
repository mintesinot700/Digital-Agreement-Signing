from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated # Ensure IsAuthenticated is imported
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserAccountsSerializers, UserLoginSerializer
from .models import UserAccounts
from rest_framework.generics import ListAPIView,CreateAPIView
from rest_framework_simplejwt.tokens import RefreshToken 

# User Registration
class User_Register(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserAccountsSerializers
    # queryset  = UserAccounts.objects.all()    

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



# User Login
class User_Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response(
                {'error': 'Both username and password is required'}, status=status.HTTP_400_BAD_REQUEST
            )
        user = authenticate(username=username,password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'access': access_token,
            'refresh': str(refresh),
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_staff, 
        },

        status=status.HTTP_200_OK)


# Accounts/views.py
class UserDeleteView(APIView):
    permission_classes = [IsAdminUser]
    def delete(self, request, pk):
        try:
            user = UserAccounts.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserAccounts.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

        # Remove refresh_token cookie
        response.delete_cookie("refresh_token")

        # If you want to also clear Django session (optional, only if sessions are used):
        if hasattr(request, "session"):
            request.session.flush()

        return response

# --- NEW ADMIN VERIFICATION VIEW ---
class AdminVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        is_admin = request.user.is_staff or request.user.is_superuser  # Check both is_staff and is_superuser
        return Response({'is_admin': is_admin}, status=status.HTTP_200_OK)

# ... (your existing Agreement-related views in a separate agreement/views.py) ...