from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserAccounts


@admin.register(UserAccounts)
class UserAccountsAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'phone_number', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('id', 'username', 'phone_number', 'email')
    ordering = ('id',)
    readonly_fields = ('id', 'created_at', 'last_login', 'date_joined')
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'created_at')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'phone_number')}),
    )
