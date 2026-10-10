"""Celery task handlers for audit."""

import structlog
from celery import shared_task
from celery.exceptions import Retry

from apps.audit.services import log_audit
from apps.inbox.services import DuplicateMessageError, is_message_processed, process_message
from apps.outbox.services_deadletter import handle_dead_letter, should_send_to_dlq

logger = structlog.get_logger(__name__)

# Exceptions that should trigger retry (transient errors)
RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, Retry)


@shared_task(
    name="audit.handle_all_messages",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_all_messages(message: dict, message_type: str) -> None:
    """Handle any message by logging to audit.

    Args:
        message: Serialized message.
        message_type: Type of the message.
    """
    correlation_id = message.get("correlation_id")
    consumer = "audit_worker"

    try:
        # Check idempotency
        if is_message_processed(consumer, correlation_id):
            logger.info(
                "Message already processed, skipping",
                consumer=consumer,
                correlation_id=str(correlation_id),
            )
            return

        # Process message
        process_message(
            consumer=consumer,
            message_id=correlation_id,
            message_type=message_type,
            payload=message,
        )

        # Log to audit
        log_audit(
            action=message_type.upper(),
            actor="system",
            entity_type=message_type.lower(),
            entity_id=correlation_id,
            changes=message,
        )

        logger.info(
            "Audit log created",
            message_type=message_type,
            correlation_id=str(correlation_id),
        )

    except DuplicateMessageError:
        logger.info(
            "Duplicate message, skipping",
            consumer=consumer,
            correlation_id=str(correlation_id),
        )
    except Exception as e:
        # Check if should send to DLQ (retry exhausted or broker error)
        if should_send_to_dlq(e):
            handle_dead_letter(
                queue_name="audit",
                message_type=message_type,
                payload=message,
                error_message=str(e),
                correlation_id=correlation_id,
                retry_count=3,  # max_retries
            )
            logger.error(
                "Sent to DLQ after retry exhaustion",
                message_type=message_type,
                correlation_id=str(correlation_id),
                error=str(e),
            )
            # Reject without requeue to prevent infinite loop
            return
        logger.exception(
            "Failed to handle message for audit",
            message_type=message_type,
            correlation_id=str(correlation_id),
        )
        raise
