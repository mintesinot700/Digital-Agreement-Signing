from django import forms
from .models import Agreement, Pdf_agreement

# NOTE: The REST API endpoints validate data through DRF serializers
# (see serializers.py). These classic Django ModelForms are kept for use in
# the Django admin or server-rendered pages, and implement the same rules.


class AgreementForm(forms.ModelForm):
    """ModelForm for the Agreement model with the same validation rules
    as AgreementSerializer."""

    class Meta:
        model = Agreement
        fields = '__all__'
        widgets = {
            'gender': forms.RadioSelect(choices=Agreement.GENDER_CHOICES),
        }

    def clean_your_name(self):
        name = self.cleaned_data.get('your_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("your_name must be at least 2 characters long.")
        return name.title()

    def clean_father_name(self):
        name = self.cleaned_data.get('father_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("father_name must be at least 2 characters long.")
        return name.title()

    def clean_grand_father_name(self):
        name = self.cleaned_data.get('grand_father_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("grand_father_name must be at least 2 characters long.")
        return name.title()

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("This field is required.")
        digits = ''.join(filter(str.isdigit, phone_number))
        if not 9 <= len(digits) <= 15:
            raise forms.ValidationError("Enter a valid phone number with 9–15 digits.")
        return phone_number.strip()

    def clean_email_account(self):
        email_account = self.cleaned_data.get('email_account')
        if not email_account:
            return email_account
        if '@' not in email_account or '.' not in email_account.split('@')[-1]:
            raise forms.ValidationError("Please enter a valid email address.")
        return email_account.strip().lower()

    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        if len(address) < 2:
            raise forms.ValidationError("Address must be at least 2 characters long.")
        return address

    def clean_city(self):
        city = self.cleaned_data.get('city', '').strip()
        if not city.replace(" ", "").replace("-", "").isalpha():
            raise forms.ValidationError("City/Town can only contain letters, spaces and hyphens.")
        return city.title()

    def clean_nationality(self):
        nationality = self.cleaned_data.get('nationality', '').strip()
        if not nationality.replace(" ", "").replace("-", "").isalpha():
            raise forms.ValidationError("Nationality can only contain letters, spaces and hyphens.")
        return nationality.title()

    def clean_signature(self):
        signature = self.cleaned_data.get('signature')
        if not signature or signature == 'data:,':
            raise forms.ValidationError("Please provide your signature.")
        return signature


class Pdf_config(forms.ModelForm):
    """ModelForm for uploading an agreement template PDF."""

    class Meta:
        model = Pdf_agreement
        fields = ['type_of_agreement', 'pdf_file']

    def clean_type_of_agreement(self):
        value = self.cleaned_data['type_of_agreement'].strip()
        if not value:
            raise forms.ValidationError("type_of_agreement cannot be empty.")
        if not value.replace(" ", "").replace("-", "").isalpha():
            raise forms.ValidationError("Please use only letters, spaces and hyphens.")
        return value

    def clean_pdf_file(self):
        pdf = self.cleaned_data.get('pdf_file')
        if not pdf:
            raise forms.ValidationError("Please upload a PDF file.")
        if not pdf.name.lower().endswith('.pdf'):
            raise forms.ValidationError("Only PDF files are allowed.")
        max_size = 5 * 1024 * 1024  # 5MB
        if pdf.size > max_size:
            raise forms.ValidationError("PDF file is too large (max 5MB).")
        return pdf
