"""Celery task handlers for payments."""

from datetime import datetime

import structlog
from celery import shared_task
from celery.exceptions import Retry

from apps.inbox.services import DuplicateMessageError, is_message_processed, process_message
from apps.messaging.messages import PaymentFailed, PaymentProcessed, StockReserved
from apps.outbox.services import create_outbox_message
from apps.outbox.services_deadletter import handle_dead_letter, should_send_to_dlq
from apps.payments.services import process_payment

logger = structlog.get_logger(__name__)

# Exceptions that should trigger retry (transient errors)
RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, Retry)


@shared_task(
    name="payments.handle_stock_reserved",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_stock_reserved(message: dict) -> None:
    """Handle StockReserved message by processing payment.

    Args:
        message: Serialized StockReserved message.
    """
    stock_reserved = StockReserved(**message)
    consumer = "payments_worker"

    try:
        # Check idempotency
        if is_message_processed(consumer, stock_reserved.correlation_id):
            logger.info(
                "Message already processed, skipping",
                consumer=consumer,
                correlation_id=str(stock_reserved.correlation_id),
            )
            return

        # Process message
        process_message(
            consumer=consumer,
            message_id=stock_reserved.correlation_id,
            message_type="StockReserved",
            payload=message,
        )

        # Get order total amount (would need to fetch from orders service)
        # For now, use a default amount
        from apps.orders.models import Order

        try:
            order = Order.objects.get(id=stock_reserved.order_id)
            amount = order.total_amount
        except Order.DoesNotExist:
            logger.error(
                "Order not found",
                order_id=str(stock_reserved.order_id),
            )
            return

        # Process payment
        try:
            payment = process_payment(
                order_id=stock_reserved.order_id,
                amount=amount,
            )

            # Emit PaymentProcessed message
            payment_processed = PaymentProcessed(
                correlation_id=stock_reserved.correlation_id,
                causation_id=stock_reserved.correlation_id,
                timestamp=datetime.now().isoformat(),
                order_id=stock_reserved.order_id,
                payment_id=payment.id,
                amount=amount,
                gateway_transaction_id=payment.gateway_transaction_id,
            )

            create_outbox_message(
                message_type="PaymentProcessed",
                payload=payment_processed.model_dump(mode="json"),
                aggregate_type="payment",
                aggregate_id=payment.id,
                correlation_id=stock_reserved.correlation_id,
                causation_id=stock_reserved.correlation_id,
            )

            logger.info(
                "Payment processed successfully",
                order_id=str(stock_reserved.order_id),
                payment_id=str(payment.id),
                amount=str(amount),
            )

        except Exception as e:
            # Emit PaymentFailed message
            payment_failed = PaymentFailed(
                correlation_id=stock_reserved.correlation_id,
                causation_id=stock_reserved.correlation_id,
                timestamp=datetime.now().isoformat(),
                order_id=stock_reserved.order_id,
                amount=amount,
                reason=str(e),
            )

            create_outbox_message(
                message_type="PaymentFailed",
                payload=payment_failed.model_dump(mode="json"),
                aggregate_type="payment",
                aggregate_id=stock_reserved.order_id,
                correlation_id=stock_reserved.correlation_id,
                causation_id=stock_reserved.correlation_id,
            )

            logger.exception(
                "Failed to process payment",
                order_id=str(stock_reserved.order_id),
            )

    except DuplicateMessageError:
        logger.info(
            "Duplicate message, skipping",
            consumer=consumer,
            correlation_id=str(stock_reserved.correlation_id),
        )
    except Exception as e:
        # Check if should send to DLQ (retry exhausted or broker error)
        if should_send_to_dlq(e):
            handle_dead_letter(
                queue_name="payments",
                message_type="StockReserved",
                payload=message,
                error_message=str(e),
                correlation_id=stock_reserved.correlation_id,
                retry_count=3,  # max_retries
            )
            logger.error(
                "Sent to DLQ after retry exhaustion",
                order_id=str(stock_reserved.order_id),
                error=str(e),
            )
            # Reject without requeue to prevent infinite loop
            return
        logger.exception(
            "Failed to handle StockReserved message",
            order_id=str(stock_reserved.order_id),
        )
        raise
