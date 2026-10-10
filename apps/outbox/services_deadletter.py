"""Services for dead letter message handling."""

import uuid

from celery.exceptions import MaxRetriesExceededError
from kombu.exceptions import OperationalError

from apps.outbox.models import DeadLetterMessage


def create_dead_letter(
    queue_name: str,
    message_type: str,
    payload: dict,
    error_message: str,
    correlation_id: uuid.UUID,
    retry_count: int = 0,
) -> DeadLetterMessage:
    """Create a dead letter message.

    Args:
        queue_name: Name of the queue where the message failed.
        message_type: Type of the message.
        payload: Message payload.
        error_message: Error message describing the failure.
        correlation_id: Correlation ID for tracing.
        retry_count: Number of retries before giving up.

    Returns:
        Created DeadLetterMessage instance.
    """
    return DeadLetterMessage.objects.create(
        queue_name=queue_name,
        message_type=message_type,
        payload=payload,
        error_message=error_message,
        correlation_id=correlation_id,
        retry_count=retry_count,
    )


def get_pending_dead_letters(
    queue_name: str | None = None, limit: int = 100
) -> list[DeadLetterMessage]:
    """Get pending dead letter messages.

    Args:
        queue_name: Optional queue name to filter by.
        limit: Maximum number of messages to return.

    Returns:
        List of pending DeadLetterMessage instances.
    """
    queryset = DeadLetterMessage.objects.filter(status=DeadLetterMessage.Status.PENDING)
    if queue_name:
        queryset = queryset.filter(queue_name=queue_name)
    return list(queryset.order_by("created_at")[:limit])


def mark_dead_letter_replayed(dead_letter_id: uuid.UUID) -> None:
    """Mark a dead letter message as replayed.

    Args:
        dead_letter_id: ID of the dead letter message.
    """
    dead_letter = DeadLetterMessage.objects.get(id=dead_letter_id)
    dead_letter.status = DeadLetterMessage.Status.REPLAYED
    dead_letter.replayed_at = dead_letter.created_at  # Will be updated in migration
    dead_letter.save()


def mark_dead_letter_discarded(dead_letter_id: uuid.UUID) -> None:
    """Mark a dead letter message as discarded.

    Args:
        dead_letter_id: ID of the dead letter message.
    """
    dead_letter = DeadLetterMessage.objects.get(id=dead_letter_id)
    dead_letter.status = DeadLetterMessage.Status.DISCARDED
    dead_letter.save()


def should_send_to_dlq(exception: Exception) -> bool:
    """Check if exception should send message to DLQ.

    Args:
        exception: The exception that occurred.

    Returns:
        True if should send to DLQ, False otherwise.
    """
    return isinstance(exception, MaxRetriesExceededError | OperationalError)


def handle_dead_letter(
    queue_name: str,
    message_type: str,
    payload: dict,
    error_message: str,
    correlation_id: uuid.UUID,
    retry_count: int = 0,
) -> DeadLetterMessage:
    """Handle a dead letter by creating a DeadLetterMessage record.

    Args:
        queue_name: Name of the queue where the message failed.
        message_type: Type of the message.
        payload: Message payload.
        error_message: Error message describing the failure.
        correlation_id: Correlation ID for tracing.
        retry_count: Number of retries before giving up.

    Returns:
        Created DeadLetterMessage instance.
    """
    return create_dead_letter(
        queue_name=queue_name,
        message_type=message_type,
        payload=payload,
        error_message=error_message,
        correlation_id=correlation_id,
        retry_count=retry_count,
    )
