"""Services for transactional outbox pattern."""

import uuid

import structlog
from django.db import transaction

from apps.outbox.models import OutboxMessage

logger = structlog.get_logger(__name__)


def create_outbox_message(
    message_type: str,
    payload: dict,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    correlation_id: uuid.UUID,
    causation_id: uuid.UUID | None = None,
) -> OutboxMessage:
    """Create an outbox message for reliable event publishing.

    Args:
        message_type: Type of the message (e.g., "OrderCreated", "StockReserved").
        payload: Message payload as dictionary.
        aggregate_type: Type of the aggregate (e.g., "order", "payment").
        aggregate_id: ID of the aggregate.
        correlation_id: Correlation ID for tracing.
        causation_id: Causation ID for message chain.

    Returns:
        The created OutboxMessage instance.
    """
    logger.info(
        "Creating outbox message",
        message_type=message_type,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id),
        correlation_id=str(correlation_id),
    )

    message = OutboxMessage.objects.create(
        message_type=message_type,
        payload=payload,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
        status=OutboxMessage.Status.PENDING,
    )

    logger.info(
        "Outbox message created successfully",
        message_id=str(message.id),
        message_type=message_type,
    )
    return message


def mark_message_published(message_id: uuid.UUID) -> OutboxMessage:
    """Mark an outbox message as published.

    Args:
        message_id: ID of the message to mark as published.

    Returns:
        The updated OutboxMessage instance.
    """
    with transaction.atomic():
        message = OutboxMessage.objects.select_for_update().get(id=message_id)
        message.status = OutboxMessage.Status.PUBLISHED
        message.published_at = transaction.now() if hasattr(transaction, "now") else None
        message.save()

    logger.info(
        "Outbox message marked as published",
        message_id=str(message_id),
    )
    return message


def mark_message_failed(message_id: uuid.UUID, error: str) -> OutboxMessage:
    """Mark an outbox message as failed.

    Args:
        message_id: ID of the message to mark as failed.
        error: Error message.

    Returns:
        The updated OutboxMessage instance.
    """
    with transaction.atomic():
        message = OutboxMessage.objects.select_for_update().get(id=message_id)
        message.status = OutboxMessage.Status.FAILED
        message.payload = {**message.payload, "_error": error}
        message.save()

    logger.error(
        "Outbox message marked as failed",
        message_id=str(message_id),
        error=error,
    )
    return message


def get_pending_messages(limit: int = 100) -> list[OutboxMessage]:
    """Get pending outbox messages for publishing.

    Args:
        limit: Maximum number of messages to retrieve.

    Returns:
        List of pending OutboxMessage instances.
    """
    with transaction.atomic():
        messages = list(
            OutboxMessage.objects.filter(status=OutboxMessage.Status.PENDING)
            .select_for_update(skip_locked=True)
            .order_by("created_at")[:limit]
        )

    logger.info(
        "Retrieved pending outbox messages",
        count=len(messages),
    )
    return messages
