from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'agreement_name', 'agreement_type', 'actor_name', 'details')
    list_filter = ('action', 'timestamp')
    search_fields = ('agreement_name', 'actor_name', 'details', 'agreement_id')
    ordering = ('-timestamp',)
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False  # audit entries are created by the system only

    def has_change_permission(self, request, obj=None):
        return False  # audit trail is immutable

    def has_delete_permission(self, request, obj=None):
        return False
