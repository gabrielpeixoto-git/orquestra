"""Celery task handlers for orchestrator (saga coordination)."""

import structlog
from celery import shared_task
from celery.exceptions import Retry
from django.utils import timezone

from apps.inbox.services import DuplicateMessageError, is_message_processed, process_message
from apps.inventory.models import StockReservation
from apps.inventory.services import release_stock
from apps.messaging.messages import (
    OrderConfirmed,
    OrderFailed,
    PaymentFailed,
    PaymentProcessed,
    StockReservationFailed,
)
from apps.orders.services import cancel_order, update_order_status
from apps.outbox.services import create_outbox_message
from apps.outbox.services_deadletter import handle_dead_letter, should_send_to_dlq

logger = structlog.get_logger(__name__)

# Exceptions that should trigger retry (transient errors)
RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, Retry)


@shared_task(
    name="orchestrator.handle_payment_processed",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_payment_processed(message: dict) -> None:
    """Handle PaymentProcessed message by confirming order.

    Args:
        message: Serialized PaymentProcessed message.
    """
    payment_processed = PaymentProcessed(**message)
    consumer = "orchestrator_worker"

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

        # Confirm order
        order = update_order_status(
            order_id=payment_processed.order_id,
            status="CONFIRMED",
        )

        # Emit OrderConfirmed message
        order_confirmed = OrderConfirmed(
            correlation_id=payment_processed.correlation_id,
            causation_id=payment_processed.correlation_id,
            timestamp=timezone.now().isoformat(),
            order_id=order.id,
            customer_id=order.customer_id,
            total_amount=order.total_amount,
        )

        create_outbox_message(
            message_type="OrderConfirmed",
            payload=order_confirmed.model_dump(mode="json"),
            aggregate_type="order",
            aggregate_id=order.id,
            correlation_id=payment_processed.correlation_id,
            causation_id=payment_processed.correlation_id,
        )

        logger.info(
            "Order confirmed successfully",
            order_id=str(order.id),
            customer_id=str(order.customer_id),
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
                queue_name="orchestrator",
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
    name="orchestrator.handle_payment_failed",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_payment_failed(message: dict) -> None:
    """Handle PaymentFailed message by cancelling order.

    Args:
        message: Serialized PaymentFailed message.
    """
    payment_failed = PaymentFailed(**message)
    consumer = "orchestrator_worker"

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

        # Cancel order
        order = cancel_order(payment_failed.order_id)

        # Compensate: release any reserved stock
        reservations = StockReservation.objects.filter(order_id=payment_failed.order_id)
        for reservation in reservations:
            try:
                release_stock(reservation.id)
                logger.info(
                    "Stock released as compensation",
                    reservation_id=str(reservation.id),
                    order_id=str(payment_failed.order_id),
                )
            except Exception:
                logger.exception(
                    "Failed to release stock during compensation",
                    reservation_id=str(reservation.id),
                    order_id=str(payment_failed.order_id),
                )

        # Emit OrderFailed message
        order_failed = OrderFailed(
            correlation_id=payment_failed.correlation_id,
            causation_id=payment_failed.correlation_id,
            timestamp=timezone.now().isoformat(),
            order_id=order.id,
            customer_id=order.customer_id,
            reason=payment_failed.reason,
            failure_step="payment",
        )

        create_outbox_message(
            message_type="OrderFailed",
            payload=order_failed.model_dump(mode="json"),
            aggregate_type="order",
            aggregate_id=order.id,
            correlation_id=payment_failed.correlation_id,
            causation_id=payment_failed.correlation_id,
        )

        logger.info(
            "Order cancelled due to payment failure",
            order_id=str(order.id),
            reason=payment_failed.reason,
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
                queue_name="orchestrator",
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


@shared_task(
    name="orchestrator.handle_stock_reservation_failed",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_stock_reservation_failed(message: dict) -> None:
    """Handle StockReservationFailed message by cancelling order.

    Args:
        message: Serialized StockReservationFailed message.
    """
    stock_failed = StockReservationFailed(**message)
    consumer = "orchestrator_worker"

    try:
        # Check idempotency
        if is_message_processed(consumer, stock_failed.correlation_id):
            logger.info(
                "Message already processed, skipping",
                consumer=consumer,
                correlation_id=str(stock_failed.correlation_id),
            )
            return

        # Process message
        process_message(
            consumer=consumer,
            message_id=stock_failed.correlation_id,
            message_type="StockReservationFailed",
            payload=message,
        )

        # Cancel order
        order = cancel_order(stock_failed.order_id)

        # Emit OrderFailed message
        order_failed = OrderFailed(
            correlation_id=stock_failed.correlation_id,
            causation_id=stock_failed.correlation_id,
            timestamp=timezone.now().isoformat(),
            order_id=order.id,
            customer_id=order.customer_id,
            reason=stock_failed.reason,
            failure_step="stock_reservation",
        )

        create_outbox_message(
            message_type="OrderFailed",
            payload=order_failed.model_dump(mode="json"),
            aggregate_type="order",
            aggregate_id=order.id,
            correlation_id=stock_failed.correlation_id,
            causation_id=stock_failed.correlation_id,
        )

        logger.info(
            "Order cancelled due to stock reservation failure",
            order_id=str(order.id),
            reason=stock_failed.reason,
        )

    except DuplicateMessageError:
        logger.info(
            "Duplicate message, skipping",
            consumer=consumer,
            correlation_id=str(stock_failed.correlation_id),
        )
    except Exception as e:
        # Check if should send to DLQ (retry exhausted or broker error)
        if should_send_to_dlq(e):
            handle_dead_letter(
                queue_name="orchestrator",
                message_type="StockReservationFailed",
                payload=message,
                error_message=str(e),
                correlation_id=stock_failed.correlation_id,
                retry_count=3,  # max_retries
            )
            logger.error(
                "Sent to DLQ after retry exhaustion",
                order_id=str(stock_failed.order_id),
                error=str(e),
            )
            # Reject without requeue to prevent infinite loop
            return
        logger.exception(
            "Failed to handle StockReservationFailed message",
            order_id=str(stock_failed.order_id),
        )
        raise
