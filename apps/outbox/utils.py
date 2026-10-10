"""Utility functions for dead letter handling."""

import uuid

import structlog

from apps.outbox.services_deadletter import create_dead_letter

logger = structlog.get_logger(__name__)


def handle_dead_letter(
    queue_name: str,
    message_type: str,
    message: dict,
    correlation_id: uuid.UUID,
    exception: Exception,
    retry_count: int = 0,
) -> None:
    """Handle a message that should go to dead letter queue.

    Args:
        queue_name: Name of the queue where the message failed.
        message_type: Type of the message.
        message: Message payload.
        correlation_id: Correlation ID for tracing.
        exception: Exception that caused the failure.
        retry_count: Number of retries before giving up.
    """
    logger.error(
        "Message failed after retries, sending to DLQ",
        queue_name=queue_name,
        message_type=message_type,
        correlation_id=str(correlation_id),
        error=str(exception),
        retry_count=retry_count,
    )

    # Create dead letter record in database
    create_dead_letter(
        queue_name=queue_name,
        message_type=message_type,
        payload=message,
        error_message=str(exception),
        correlation_id=correlation_id,
        retry_count=retry_count,
    )
