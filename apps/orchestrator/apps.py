"""Django app configuration for orchestrator."""

from django.apps import AppConfig


class OrchestratorConfig(AppConfig):
    """Configuration for orchestrator app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orchestrator"
