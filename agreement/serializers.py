from rest_framework import serializers
from PIL import Image
import os
import re
from .models import Agreement, AuditLog, Pdf_agreement


class Pdf_agreementSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Pdf_agreement
        fields = ['id', 'type_of_agreement', 'pdf_file', 'pdf_url']

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/pdf/{obj.id}/')
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
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    submitted_by = serializers.CharField(source='user.username', read_only=True, default=None)

    pdf_agreement = serializers.PrimaryKeyRelatedField(
        queryset=Pdf_agreement.objects.all(),
        required=True,
        allow_null=False
    )

    class Meta:
        model = Agreement
        fields = '__all__'
        read_only_fields = ['submited_date', 'user', 'pdf_agreement_name']
        # The model gives these ImageFields a default, which makes DRF treat
        # them as optional; a signing platform must always receive them.
        extra_kwargs = {
            'signature': {'required': True, 'allow_null': False},
            'profile_photo': {'required': True, 'allow_null': False},
            'photo_of_userID': {'required': True, 'allow_null': False},
        }

    def validate(self, attrs):
        pdf_agreement = attrs.get('pdf_agreement')
        if pdf_agreement and not pdf_agreement.type_of_agreement:
            raise serializers.ValidationError(
                {"pdf_agreement": "Selected agreement has no type_of_agreement."}
            )
        return attrs

    def create(self, validated_data):
        pdf_agreement_instance = validated_data.get('pdf_agreement')
        pdf_agreement_name = (
            pdf_agreement_instance.type_of_agreement if pdf_agreement_instance else None
        )
        if not pdf_agreement_name:
            raise serializers.ValidationError(
                {"pdf_agreement": "Selected agreement has no type_of_agreement."}
            )

        instance = Agreement.objects.create(
            **validated_data,
            pdf_agreement_name=pdf_agreement_name
        )
        return instance

    def _clean_name(self, value, field_label):
        value = value.strip()
        if not re.fullmatch(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError(f"{field_label} can only contain letters and spaces")
        if len(value) < 2:
            raise serializers.ValidationError(f"{field_label} must be at least 2 characters long")
        return value.title()

    def validate_your_name(self, value):
        return self._clean_name(value, "your_name")

    def validate_father_name(self, value):
        return self._clean_name(value, "father_name")

    def validate_grand_father_name(self, value):
        return self._clean_name(value, "grand_father_name")

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
        # EmailField already validated the format; just normalise.
        return value.strip().lower()

    def validate_phone_number(self, value):
        digits = ''.join(filter(str.isdigit, value))
        if 9 <= len(digits) <= 15:
            return value.strip()
        raise serializers.ValidationError("Enter a valid phone number with 9–15 digits.")

    def _validate_image(self, value, field_name, allowed_extensions):
        if not value:
            raise serializers.ValidationError(f"No {field_name} provided.")
        extension = os.path.splitext(value.name)[1].lower()
        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file extension for {field_name}. Allowed: {', '.join(allowed_extensions)}"
            )
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"{field_name} is too large. Max size is {max_size / 1024 / 1024:.0f}MB"
            )
        try:
            img = Image.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError(f"Invalid image file for {field_name}.")
        return value

    def validate_profile_photo(self, value):
        return self._validate_image(value, "profile photo", ['.jpg', '.jpeg', '.png', '.gif'])

    def validate_photo_of_userID(self, value):
        return self._validate_image(value, "user ID photo", ['.jpg', '.jpeg', '.png', '.gif'])

    def validate_signature(self, value):
        # The frontend signature pad produces PNG data; accept PNG (+ other images
        # for users who still upload a scanned signature).
        return self._validate_image(value, "signature", ['.png', '.jpg', '.jpeg'])

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.username', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'agreement_id', 'agreement_name', 'agreement_type',
            'action', 'actor', 'actor_name', 'details', 'timestamp',
        ]
