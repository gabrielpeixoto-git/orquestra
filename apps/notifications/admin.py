from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "recipient", "type", "status", "subject", "created_at"]
    list_filter = ["type", "status", "created_at"]
    search_fields = ["id", "recipient", "subject"]
