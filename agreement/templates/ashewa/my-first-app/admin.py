from django.contrib import admin
from .models import Agreement


# admin.site.register(Agreement)

class AgreementAdmin(admin.ModelAdmin):
    search_fields = ( "your_name",'email_account','phone_number')
    list_display = ('id','your_name', 'father_name','grand_father_name','gender','phone_number','email_account', 'nationality','city','address', 'signature', 'photo_of_userID','pdf_agreement', 'user')
    search_fields = ('your_name','id',)
    ordering = 'id',
    list_filter	 = "your_name",'email_account','phone_number'
    readonly_fields = ("id",)

admin.site.register(Agreement,AgreementAdmin)
