from django.forms import ModelForm , forms 
from .models import UserAccounts
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re


class UserAccountsForm(ModelForm):
    class Meta:
        model = UserAccounts
        fields = ["username", "email", "password", "phone_number"]

    username = forms.CharField(max_length=150, 
                               required=True,
                               validators=[
                                RegexValidator(
                                    regex=r'^[a-zA-Z\s]+$',
                                    message='Name can only contain letters and spaces'
                                )
                  ])    

    def clean_username(self,value):
        username = self.cleaned_data.get('username')
        if "admin" == value:
            raise ValidationError("Username cannot be admin")
        elif len(value)< 3:
            raise ValidationError("your username has at least 3 character.")
        return value

    def clean_email(self,value):
        email = self.cleaned_data.get('email')
        if "@" and "." in value:  
            if not value.count('@') == 1 or not value.count('.') >= 1:
                raise ValidationError("please enter valid email.")
        return value


    def clean_password(self,value):
        password = self.cleaned_data.get('password')
       
        if len(value)<=6:
            raise ValidationError("your password must at least 6 long.")
        return value

    def clean_phone_number(self, value):
            phone_regex = self.cleaned_data.get('phone_number')
            phone_regex = re.compile(r'^(\+?1?[ -]?)?(\([0-9]{3}\)|[0-9]{3})[ -]?[0-9]{3}[ -]?[0-9]{4}$'
)
            if phone_regex.match(value):
                return value
            else:
                raise ValidationError("Enter a valid phone number.")

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    


        

        