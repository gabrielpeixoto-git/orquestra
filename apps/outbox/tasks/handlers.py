"""Celery task handlers for dead letter queue processing."""

import uuid

import structlog
from celery import shared_task

from apps.outbox.services_deadletter import create_dead_letter

logger = structlog.get_logger(__name__)


@shared_task(name="outbox.handle_dlq_message")
def handle_dlq_message(message: dict, queue_name: str) -> None:
    """Handle dead letter message by storing in database.

    Args:
        message: Serialized message from DLQ.
        queue_name: Name of the original queue where the message failed.
    """
    correlation_id = message.get("correlation_id")
    message_type = message.get("message_type", "unknown")
    error_message = message.get("error_message", "Unknown error")
    retry_count = message.get("retry_count", 0)

    logger.info(
        "Processing DLQ message",
        queue_name=queue_name,
        message_type=message_type,
        correlation_id=str(correlation_id),
    )

    try:
        create_dead_letter(
            queue_name=queue_name,
            message_type=message_type,
            payload=message,
            error_message=error_message,
            correlation_id=correlation_id if correlation_id else uuid.uuid4(),
            retry_count=retry_count,
        )

        logger.info(
            "DLQ message stored in database",
            queue_name=queue_name,
            message_type=message_type,
        )
    except Exception:
        logger.exception(
            "Failed to store DLQ message in database",
            queue_name=queue_name,
            message_type=message_type,
        )
        raise
