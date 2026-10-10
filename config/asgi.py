"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_asgi_application()

# Configure logging after Django loads
from apps.core.logging_config import configure_logging

configure_logging()

# Configure OpenTelemetry after Django loads
from apps.core.otel_config import configure_opentelemetry

configure_opentelemetry()
