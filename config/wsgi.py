"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_wsgi_application()

# Configure logging after Django loads
from apps.core.logging_config import configure_logging

configure_logging()

# Configure OpenTelemetry after Django loads
from apps.core.otel_config import configure_opentelemetry

configure_opentelemetry()
