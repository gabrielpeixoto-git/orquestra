"""Celery task handlers for notifications."""

from datetime import datetime

import structlog
from celery import shared_task
from celery.exceptions import Retry

from apps.inbox.services import DuplicateMessageError, is_message_processed, process_message
from apps.messaging.messages import (
    NotificationSent,
    PaymentFailed,
    PaymentProcessed,
)
from apps.notifications.services import send_notification
from apps.outbox.services import create_outbox_message
from apps.outbox.services_deadletter import handle_dead_letter, should_send_to_dlq

logger = structlog.get_logger(__name__)

# Exceptions that should trigger retry (transient errors)
RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, Retry)


@shared_task(
    name="notifications.handle_payment_processed",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_payment_processed(message: dict) -> None:
    """Handle PaymentProcessed message by sending notification.

    Args:
        message: Serialized PaymentProcessed message.
    """
    payment_processed = PaymentProcessed(**message)
    consumer = "notifications_worker"

    try:
        # Check idempotency
        if is_message_processed(consumer, payment_processed.correlation_id):
            logger.info(
                "Message already processed, skipping",
                consumer=consumer,
                correlation_id=str(payment_processed.correlation_id),
            )
            return

        # Process message
        process_message(
            consumer=consumer,
            message_id=payment_processed.correlation_id,
            message_type="PaymentProcessed",
            payload=message,
        )

        # Send notification
        notification = send_notification(
            recipient="customer@example.com",  # Would fetch from order
            notification_type="EMAIL",
            subject="Payment Successful",
            body=f"Your payment of {payment_processed.amount} was successful.",
        )

        # Emit NotificationSent message
        notification_sent = NotificationSent(
            correlation_id=payment_processed.correlation_id,
            causation_id=payment_processed.correlation_id,
            timestamp=datetime.now().isoformat(),
            notification_id=notification.id,
            recipient=notification.recipient,
            notification_type=notification.type,
            subject=notification.subject,
        )

        create_outbox_message(
            message_type="NotificationSent",
            payload=notification_sent.model_dump(mode="json"),
            aggregate_type="notification",
            aggregate_id=notification.id,
            correlation_id=payment_processed.correlation_id,
            causation_id=payment_processed.correlation_id,
        )

        logger.info(
            "Notification sent successfully",
            notification_id=str(notification.id),
            order_id=str(payment_processed.order_id),
        )

    except DuplicateMessageError:
        logger.info(
            "Duplicate message, skipping",
            consumer=consumer,
            correlation_id=str(payment_processed.correlation_id),
        )
    except Exception as e:
        # Check if should send to DLQ (retry exhausted or broker error)
        if should_send_to_dlq(e):
            handle_dead_letter(
                queue_name="notifications",
                message_type="PaymentProcessed",
                payload=message,
                error_message=str(e),
                correlation_id=payment_processed.correlation_id,
                retry_count=3,  # max_retries
            )
            logger.error(
                "Sent to DLQ after retry exhaustion",
                order_id=str(payment_processed.order_id),
                error=str(e),
            )
            # Reject without requeue to prevent infinite loop
            return
        logger.exception(
            "Failed to handle PaymentProcessed message",
            order_id=str(payment_processed.order_id),
        )
        raise


@shared_task(
    name="notifications.handle_payment_failed",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_payment_failed(message: dict) -> None:
    """Handle PaymentFailed message by sending notification.

    Args:
        message: Serialized PaymentFailed message.
    """
    payment_failed = PaymentFailed(**message)
    consumer = "notifications_worker"

    try:
        # Check idempotency
        if is_message_processed(consumer, payment_failed.correlation_id):
            logger.info(
                "Message already processed, skipping",
                consumer=consumer,
                correlation_id=str(payment_failed.correlation_id),
            )
            return

        # Process message
        process_message(
            consumer=consumer,
            message_id=payment_failed.correlation_id,
            message_type="PaymentFailed",
            payload=message,
        )

        # Send notification
        notification = send_notification(
            recipient="customer@example.com",
            notification_type="EMAIL",
            subject="Payment Failed",
            body=f"Your payment of {payment_failed.amount} failed: {payment_failed.reason}",
        )

        logger.info(
            "Payment failure notification sent",
            notification_id=str(notification.id),
            order_id=str(payment_failed.order_id),
        )

    except DuplicateMessageError:
        logger.info(
            "Duplicate message, skipping",
            consumer=consumer,
            correlation_id=str(payment_failed.correlation_id),
        )
    except Exception as e:
        # Check if should send to DLQ (retry exhausted or broker error)
        if should_send_to_dlq(e):
            handle_dead_letter(
                queue_name="notifications",
                message_type="PaymentFailed",
                payload=message,
                error_message=str(e),
                correlation_id=payment_failed.correlation_id,
                retry_count=3,  # max_retries
            )
            logger.error(
                "Sent to DLQ after retry exhaustion",
                order_id=str(payment_failed.order_id),
                error=str(e),
            )
            # Reject without requeue to prevent infinite loop
            return
        logger.exception(
            "Failed to handle PaymentFailed message",
            order_id=str(payment_failed.order_id),
        )
        raise
