from django import forms
from .models import UserAccounts


class UserAccountsForm(forms.ModelForm):
    """ModelForm for creating/updating user accounts with sensible validation.
    (The REST API validates through DRF serializers; this form is for
    admin/server-rendered usage.)"""

    class Meta:
        model = UserAccounts
        fields = ["username", "email", "phone_number"]

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username.lower() == 'admin':
            raise forms.ValidationError("Username cannot be 'admin'.")
        if len(username) < 3:
            raise forms.ValidationError("Your username must have at least 3 characters.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            raise forms.ValidationError("Please enter a valid email address.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if not phone_number:
            return phone_number
        digits = ''.join(filter(str.isdigit, phone_number))
        if not 9 <= len(digits) <= 15:
            raise forms.ValidationError("Enter a valid phone number with 9–15 digits.")
        return phone_number
