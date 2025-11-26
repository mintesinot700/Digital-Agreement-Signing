from django import forms 
from .models import Agreement , Pdf_agreement
from rest_framework import serializers
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError
import re 

# Form for the Agreement model
class AgreementForm(forms.ModelForm):
    class Meta:
        model= Agreement
        fields = '__all__'
        widgets = {
            'gender': forms.RadioSelect(choices=Agreement.GENDER_CHOICES),
        }

# validate contact_info field
    def validate_phone_number(self, value):

            phone_regex = re.compile(r'^(\+?1?[ -]?)?(\([0-9]{3}\)|[0-9]{3})[ -]?[0-9]{3}[ -]?[0-9]{4}$'
)
            if phone_regex.match(value):
                return value
            else:
                raise ValidationError("Enter a phone number.")

    def validate_email_account(self, value):
        try:
            validate_email(value)
            return value
        except ValidationError:
                raise ValidationError("Enter a valid email or phone number.")

# validate signature field    
    def validate_signature(self, file):
        try:
            img = Image.open(file)
            img.verify()  
        except Exception:
            raise serializers.ValidationError("please uploaded signature.")

        return file
            
# clean the agreement field
   
    def clean_save_agreement(self): 
        name = self.cleaned_data.get('save_agreement')
        if len(name)<2:
            raise forms.ValidationError("title must be at least 3 charaters long.")
        return name
    def clean_your_name(self): 
        name = self.cleaned_data.get('your_name')
        if len(name)<2:
            raise forms.ValidationError("your_name must be at least 3 charaters long.")
        return name

    def clean_father_name(self): 
        name = self.cleaned_data.get('father_name')
        if len(name)<2:
            raise forms.ValidationError("father_name must be at least 3 charaters long.")
        return name

    def clean_grand_father_name(self): 
        name = self.cleaned_data.get('grand_father_name')
        if len(name)<3:
            raise forms.ValidationError("grand_father_name' must be at least 3 charaters long.")
        return name
    
    def clean_phone_number(self):
        Phone_number = self.cleaned_data.get('phone_number') 
        if not Phone_number:
            raise forms.ValidationError("This field is requied.")
        return self.validate_phone_number(Phone_number)

    def clean_email_account(self):
        Email_account = self.cleaned_data.get('email_account') 
        if not Email_account:
            raise forms.ValidationError("This field is requied.")
        return self.validate_Email_account(Email_account)
        
        if Agreement.objects.filter(Email_account=email_account).exists():
             raise ValueError("This email already exists!")
        return self.validate_email_account(Email_account)

    def clean_address(self):
        address = self.cleaned_data['address'].strip()
        if len(address) < 2:
            raise forms.ValidationError("Address must be at least 10 characters long.")
        return address

    def clean_city(self):
        city = self.cleaned_data['city'].strip()
        if not city.replace(" ", "").replace("-", "").isalpha():
            raise forms.ValidationError("City/Town can only contain letters, spaces and hyphens.")
        return city

    def clean_nationality(self):
        nationality = self.cleaned_data['nationality'].strip()
        if not nationality.replace(" ", "").replace("-", "").isalpha():
            raise forms.ValidationError("Nationality can only contain letters, spaces and hyphens.")
        return nationality.title()

    def clean_signature(self):
        signature = self.cleaned_data.get('signature')
        if not signature or signature == 'data:,':
            raise forms.ValidationError(('Please provide your signature'))
        return signature

    def clean_agreement_paper_file(self):
        pdf = self.cleaned_data.get('agreement_Paper_file')


        if not pdf.name.endswith('.pdf'):
            raise ValidationError("Only PDF files are allowed.")


        max_size = 5 * 1024 * 1024  
        if pdf.size > max_size:
            raise ValidationError("PDF file is too large (max 5MB).")

        return pdf

    def clean_agreement(self):
        agreement = self.cleaned_data.get("agreement")
        return agreement
     
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    
# Form for Pdf_agreement model    
class Pdf_agreementForm(forms.ModelForm):

    class Meta:
        model = Pdf_agreement
        fields= ['type_of_agreement','pdf_file']

    def clean_type_of_agreement(self):
        type = self.cleaned_data['type_of_agreement'].strip()
        if not type.replace(" ", "").replace("-", "").isalpha():
            raise forms.ValidationError("please, use only contain letters, spaces and hyphens.")
        return type
    
    def clean_pdf_file(self):
        pdf = self.cleaned_data.get('pdf_file')


        if not pdf.name.endswith('.pdf'):
            raise ValidationError("Only PDF files are allowed.")


        max_size = 5 * 1024 * 1024  
        if pdf.size > max_size:
            raise ValidationError("PDF file is too large (max 5MB).")

        return pdf

    def clean_Pdf_agreement(self):
        agreement = self.cleaned_data.get("Pdf_agreement")
        return agreement
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    



