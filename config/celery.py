"""Celery configuration for Orquestra."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("orquestra")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Configure logging after Django settings are loaded
from apps.core.logging_config import configure_logging

configure_logging()

# Configure OpenTelemetry after Django settings are loaded
from apps.core.otel_config import configure_opentelemetry

configure_opentelemetry()


app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    broker_url="amqp://guest:guest@localhost:5672/%2F",
    result_backend="redis://localhost:6379/0",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
    task_retry_backoff=True,
    task_retry_backoff_max=600,
    task_retry_jitter=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "watchdog-saga-timeouts": {
            "task": "orchestrator.watchdog_saga_timeouts",
            "schedule": 300.0,  # Run every 5 minutes
        },
    },
    task_queues={
        "inventory": {
            "exchange": "orquestra",
            "exchange_type": "topic",
            "routing_key": "order.ordercreated",
            "queue_arguments": {"x-queue-type": "quorum"},
        },
        "payments": {
            "exchange": "orquestra",
            "exchange_type": "topic",
            "routing_key": "inventory.stockreserved",
            "queue_arguments": {"x-queue-type": "quorum"},
        },
        "notifications": {
            "exchange": "orquestra",
            "exchange_type": "topic",
            "routing_key": "payments.*",
            "queue_arguments": {"x-queue-type": "quorum"},
        },
        "audit": {
            "exchange": "orquestra",
            "exchange_type": "topic",
            "routing_key": "#",
            "queue_arguments": {"x-queue-type": "quorum"},
        },
        "orchestrator": {
            "exchange": "orquestra",
            "exchange_type": "topic",
            "routing_key": "payments.*",
            "queue_arguments": {"x-queue-type": "quorum"},
        },
        "orchestrator_inventory": {
            "exchange": "orquestra",
            "exchange_type": "topic",
            "routing_key": "inventory.stockreservationfailed",
            "queue_arguments": {"x-queue-type": "quorum"},
        },
    },
    task_default_queue="default",
    task_default_exchange="orquestra",
    task_default_exchange_type="topic",
    task_default_routing_key="default",
    task_routes={
        "apps.inventory.tasks.*": {"queue": "inventory"},
        "apps.payments.tasks.*": {"queue": "payments"},
        "apps.notifications.tasks.*": {"queue": "notifications"},
        "apps.audit.tasks.*": {"queue": "audit"},
        "apps.orchestrator.tasks.*": {"queue": "orchestrator"},
        "apps.outbox.tasks.*": {"queue": "outbox"},
    },
)
