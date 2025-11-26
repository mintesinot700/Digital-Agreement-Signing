from rest_framework import serializers
from .models import UserAccounts
from agreement.serializers import AgreementSerializer
from django.core.validators import RegexValidator, validate_email


class UserAccountsSerializers(serializers.ModelSerializer):
    agreement = AgreementSerializer(read_only = True, many = True)
    password = serializers.CharField(max_length = 100)
    
    class Meta:
        model = UserAccounts
        fields = ["id","username", "email", "password", "phone_number","agreement",'is_active','is_staff','created_at'] 
        extra_kwargs = {
            'password': {'write_only': True}, 
            'agreement': {'read_only': True}, 
        }
  
    
    email = serializers.EmailField(
        required=True,
        validators=[validate_email]
    )
    phone_number = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be in the format: '+999999999'. Up to 15 digits."
            )
        ]
    )
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z][a-zA-Z0-9_\.]*$',  # Allows alphanumeric with _ and .
                message='Username must start with a letter and contain only letters, numbers, underscores, and periods.'
            )
        ]
    )


    def create(self, validated_data):
        user = UserAccounts.objects.create_user(
            username = validated_data['username'],
            email = validated_data['email'],
            password = validated_data.get("password",None),
            phone_number = validated_data['phone_number'],
            )
        return user
    
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        trim_whitespace=False  
    )

    def validate_username(self, value):
        return value.lower()