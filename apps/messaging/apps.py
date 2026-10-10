"""Django app configuration for messaging."""

from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """Configuration for messaging app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messaging"
