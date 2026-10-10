from django.contrib import admin

from .models import InboxMessage


@admin.register(InboxMessage)
class InboxMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "consumer", "message_id", "message_type", "processed_at"]
    list_filter = ["consumer", "processed_at"]
    search_fields = ["id", "message_id"]
    readonly_fields = ["id", "consumer", "message_id", "message_type", "payload", "processed_at"]
