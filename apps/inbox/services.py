"""Services for inbox pattern (idempotent message processing)."""

import uuid

import structlog
from django.db import transaction

from apps.inbox.models import InboxMessage

logger = structlog.get_logger(__name__)


class DuplicateMessageError(Exception):
    """Error raised when message is already processed."""


def process_message(
    consumer: str,
    message_id: uuid.UUID,
    message_type: str,
    payload: dict,
) -> InboxMessage:
    """Process a message idempotently.

    Args:
        consumer: Consumer identifier (e.g., "inventory_worker").
        message_id: ID of the message.
        message_type: Type of the message.
        payload: Message payload.

    Returns:
        The created InboxMessage instance.

    Raises:
        DuplicateMessageError: If message was already processed.
    """
    logger.info(
        "Processing message",
        consumer=consumer,
        message_id=str(message_id),
        message_type=message_type,
    )

    try:
        with transaction.atomic():
            # Try to create inbox message
            inbox_message = InboxMessage.objects.create(
                consumer=consumer,
                message_id=message_id,
                message_type=message_type,
                payload=payload,
            )

        logger.info(
            "Message processed successfully",
            inbox_id=str(inbox_message.id),
            consumer=consumer,
            message_id=str(message_id),
        )
        return inbox_message

    except Exception as e:
        # Check if it's a duplicate
        if InboxMessage.objects.filter(
            consumer=consumer,
            message_id=message_id,
        ).exists():
            logger.warning(
                "Message already processed",
                consumer=consumer,
                message_id=str(message_id),
            )
            raise DuplicateMessageError(
                f"Message {message_id} already processed by {consumer}"
            ) from e
        raise


def is_message_processed(consumer: str, message_id: uuid.UUID) -> bool:
    """Check if a message was already processed by a consumer.

    Args:
        consumer: Consumer identifier.
        message_id: ID of the message.

    Returns:
        True if message was processed, False otherwise.
    """
    exists = InboxMessage.objects.filter(
        consumer=consumer,
        message_id=message_id,
    ).exists()

    logger.debug(
        "Checking if message processed",
        consumer=consumer,
        message_id=str(message_id),
        processed=exists,
    )
    return exists
