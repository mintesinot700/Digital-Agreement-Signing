from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator, MinLengthValidator
from Accounts.models import UserAccounts
import re


# Models class for agreemnt form
class Pdf_agreement(models.Model):
    type_of_agreement = models.CharField(
        max_length=300,
        # Corrected help_text
        help_text="The type or title of the agreement (e.g., 'Rental Agreement')."
    )
    
    pdf_file = models.FileField(
        upload_to='media/PDF_file',
        blank=False,
        default='unknown',
        null=False,
        validators=[
            FileExtensionValidator(['pdf', 'PDF']),
        ]
    )

    def __str__(self):
        return self.type_of_agreement

class Agreement(models.Model):
    
    GENDER_CHOICES=[
        ('M',"Male"),
        ('F',"Female"),
    ]

    STATUS_CHOICES=[
        ('approved',"Approved"),
        ('rejected',"Rejected"),
        ('pending',"Pending"),
    ]

# Owner of the agreement
    user = models.ForeignKey(
        UserAccounts, 
        on_delete=models.CASCADE, 
        null=True, 
        related_name='agreement',
    )
    
# ForeignKey to the Pdf_agreement model
    pdf_agreement = models.ForeignKey(
        Pdf_agreement,
        on_delete=models.SET_NULL,  # Good practice to prevent data loss
        null=True,  # Allows the field to be null if the referenced object is deleted
        blank=False, # We'll make this required in the form
        related_name='agreements_submitted',
        help_text='The specific agreement template this form is for.'
    )
    
    pdf_agreement_name = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="The name of the agreement template at the time of submission."
    )
# Profile photo of the user 
    profile_photo = models.ImageField(
        upload_to='images/Profile_photo',
        blank=False,
        null=False,
        default='unknown',
        db_column='profile_photo'
    )
    
# Your_name of the user
    your_name = models.CharField(
        blank=False,
        null=False,
        max_length=200,
        default="Unknown", 
        help_text='Enter your Your_name',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]+$',
                message='Name can only contain letters and spaces'
            )
        ])  

# Father_name of the user
    father_name = models.CharField(
        blank=False,
        null=False,
        default='unknown',
        max_length=200, 
        help_text='Enter your Father_name',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]+$',
                message='Name can only contain letters and spaces'
            )
        ])

# Grand_Father_name of the user 
    grand_father_name = models.CharField(
        blank=False,
        null=False,
        max_length=200,
        default="Unknown", 
        help_text='Enter your Grand_Father_name',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]+$',
                message='Name can only contain letters and spaces'
            )
        ]) 
# Gender of the user 
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='M', # Corrected default to be a valid choice
    )

# Address of user
    address = models.CharField(
        max_length=200,
        default='unknown',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\.,#]+$',
                message="Address can only contain letters, numbers, spaces, and -.,#"
            )
        ],
        help_text="Street address, building, apartment, etc."
    )

# City/town of user    
    city = models.CharField(
        max_length=100,
        default='unknown',
        validators=[
            MinLengthValidator(2),
            RegexValidator(
                regex=r'^[a-zA-Z\s\-]+$',
                message="City name can only contain letters, spaces, and hyphens."
            )
        ],
        help_text="City or town name"
    )

# Nationality of user    
    nationality = models.CharField(
        max_length=100,
        default='unknown',
        validators=[
            MinLengthValidator(2),
            RegexValidator(
                regex=r'^[a-zA-Z\s\-]+$',
                message="Nationality can only contain letters, spaces, and hyphens."
            )
        ],
        help_text="Person's nationality (e.g., American, British)"
    )

# Phone_number of user 
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."  
    )
    phone_number = models.CharField(
        blank=False,
        default='unknown',
        null=False,
        max_length=17, 
        help_text='Enter you Phone_number',
        validators=[phone_regex]
    )

# Email_account of user 
    email_account = models.EmailField(
        blank=True,
        null=True,
        max_length=200, 
        help_text='Enter you Email_account',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                message='Enter a valid email address.' # Corrected error message
            )
        ])
        
# Submited_date of the Agreement
    submited_date = models.DateTimeField(auto_now_add=True)

# Photo_of_userID
    photo_of_userID = models.ImageField(
        upload_to='images/userID_photo',
        blank=False,
        null=False,
        default='unknown', 
    )
        
# Signature of the user 
    signature = models.ImageField(
        upload_to='images/signatures', 
        blank=False, 
        default='unknown',
        null=False,
    )

# Status of the agreement
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
    ) 

    def __str__(self):
        return f"{self.your_name}'s Agreement"