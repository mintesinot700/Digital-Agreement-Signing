from rest_framework import serializers
from django.core.exceptions import ValidationError
from PIL import Image
import os
import re
from .models import Agreement, Pdf_agreement
from django.urls import reverse

class Pdf_agreementSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Pdf_agreement
        fields = ['id', 'type_of_agreement', 'pdf_file', 'pdf_url']

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                reverse('pdf_file_view', args=[obj.id])
            )
        return None

    def validate_type_of_agreement(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("type_of_agreement cannot be empty")
        if not re.fullmatch(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("type_of_agreement can only contain letters and spaces")
        return value

    def validate_pdf_file(self, value):
        if hasattr(value, 'content_type') and value.content_type != 'application/pdf':
            raise serializers.ValidationError('Uploaded file must be a valid PDF.')
        header = value.read(4)
        value.seek(0)
        if header != b'%PDF':
            raise serializers.ValidationError('File is not a valid PDF document.')
        return value

class AgreementSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(
        source='get_gender_display',
        read_only=True
    )
    
    pdf_agreement_name = serializers.CharField(read_only=True)  # Keep read-only for API output
    
    pdf_agreement = serializers.PrimaryKeyRelatedField(
        queryset=Pdf_agreement.objects.all(),
        required=True,
        allow_null=False
    )

    class Meta:
        model = Agreement
        fields = '__all__'
        read_only_fields = ['submited_date', 'user', 'pdf_agreement_name']

    def validate(self, attrs):
        print("Serializer validated attrs:", attrs)  # Debug
        pdf_agreement = attrs.get('pdf_agreement')
        if pdf_agreement and not pdf_agreement.type_of_agreement:
            raise serializers.ValidationError({"pdf_agreement": "Selected agreement has no type_of_agreement."})
        return attrs

    def create(self, validated_data):
        print("Creating Agreement with validated data:", validated_data)  # Debug
        pdf_agreement_instance = validated_data.get('pdf_agreement')
        
        # Explicitly set pdf_agreement_name for the instance
        pdf_agreement_name = pdf_agreement_instance.type_of_agreement if pdf_agreement_instance else None
        print("Setting pdf_agreement_name to:", pdf_agreement_name)  # Debug
        
        if not pdf_agreement_name:
            raise serializers.ValidationError({"pdf_agreement": "Selected agreement has no type_of_agreement."})

        # Create the instance with pdf_agreement_name
        instance = Agreement.objects.create(
            **validated_data,
            pdf_agreement_name=pdf_agreement_name
        )
        print("Created Agreement with pdf_agreement_name:", instance.pdf_agreement_name)  # Debug
        return instance

    def validate_your_name(self, value):
        value = value.strip()
        if not re.fullmatch(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("your_name can only contain letters and spaces")
        if len(value) < 2:
            raise serializers.ValidationError("your_name must be at least 2 characters long")
        return value.title()

    def validate_father_name(self, value):
        value = value.strip()
        if not re.fullmatch(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("father_name can only contain letters and spaces")
        if len(value) < 2:
            raise serializers.ValidationError("father_name must be at least 2 characters long")
        return value.title()

    def validate_grand_father_name(self, value):
        value = value.strip()
        if not re.fullmatch(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("grand_father_name can only contain letters and spaces")
        if len(value) < 2:
            raise serializers.ValidationError("grand_father_name must be at least 2 characters long")
        return value.title()

    def validate_nationality(self, value):
        value = value.strip()
        if not value.replace(" ", "").replace("-", "").isalpha():
            raise serializers.ValidationError(
                "Nationality must contain only letters, spaces and hyphens."
            )
        return value.title()

    def validate_city(self, value):
        value = value.strip()
        if not value.replace(" ", "").replace("-", "").isalpha():
            raise serializers.ValidationError(
                "City must contain only letters, spaces and hyphens."
            )
        return value.title()

    def validate_address(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError(
                "Address must be at least 2 characters long."
            )
        return value

    def validate_email_account(self, value):
        value = value.strip()
        if '@' in value:
            if value.count('@') != 1 or not value.endswith('.com'):
                raise serializers.ValidationError('Please enter a valid email address.')
            return value
        raise serializers.ValidationError('Please enter a valid email address.')

    def validate_phone_number(self, value):
        digits = ''.join(filter(str.isdigit, value))
        if 10 <= len(digits) <= 15:
            return value
        raise serializers.ValidationError("Enter a valid phone number with 10–15 digits.")

    def _validate_image(self, value, field_name):
        if not value:
            raise serializers.ValidationError(f"No {field_name} provided.")
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        extension = os.path.splitext(value.name)[1].lower()
        if extension not in valid_extensions:
            raise serializers.ValidationError(
                f"Unsupported file extension for {field_name}. Allowed: {', '.join(valid_extensions)}"
            )
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(f"{field_name} is too large. Max size is {max_size/1024/1024}MB")
        try:
            img = Image.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError(f"Invalid image file for {field_name}.")
        return value

    def validate_profile_photo(self, value):
        return self._validate_image(value, "profile photo")

    def validate_photo_of_userID(self, value):
        return self._validate_image(value, "user ID photo")

    def validate_signature(self, value):
        return self._validate_image(value, "signature")

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)