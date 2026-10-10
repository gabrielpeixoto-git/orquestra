from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["id", "action", "actor", "entity_type", "entity_id", "timestamp"]
    list_filter = ["action", "timestamp"]
    search_fields = ["id", "actor", "entity_id"]
    readonly_fields = ["id", "action", "actor", "entity_type", "entity_id", "changes", "timestamp"]
