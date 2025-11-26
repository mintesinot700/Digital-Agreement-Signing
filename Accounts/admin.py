from django.contrib import admin
from .models import UserAccounts




class UserListAdmin(admin.ModelAdmin):
    list_display = ('id','username','email','phone_number','password',"created_at")
    list_filter = ('username','phone_number')
    search_fields = ('id','username','phone_number','email')
    ordering = 'id',
    readonly_fields = ("id",)



admin.site.register(UserAccounts, UserListAdmin)