"""Celery task handlers for inventory."""

from datetime import datetime

import structlog
from celery import shared_task
from celery.exceptions import Retry

from apps.inbox.services import DuplicateMessageError, is_message_processed, process_message
from apps.inventory.services import reserve_stock
from apps.messaging.messages import OrderCreated
from apps.outbox.services import create_outbox_message
from apps.outbox.services_deadletter import handle_dead_letter, should_send_to_dlq

logger = structlog.get_logger(__name__)

# Exceptions that should trigger retry (transient errors)
RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, Retry)


@shared_task(
    name="inventory.handle_order_created",
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def handle_order_created(message: dict) -> None:
    """Handle OrderCreated message by reserving stock.

    Args:
        message: Serialized OrderCreated message.
    """
    order_created = OrderCreated(**message)
    consumer = "inventory_worker"

    try:
        # Check idempotency
        if is_message_processed(consumer, order_created.correlation_id):
            logger.info(
                "Message already processed, skipping",
                consumer=consumer,
                correlation_id=str(order_created.correlation_id),
            )
            return

        # Process message
        process_message(
            consumer=consumer,
            message_id=order_created.correlation_id,
            message_type="OrderCreated",
            payload=message,
        )

        # Reserve stock for each item
        for item in order_created.items:
            try:
                reservation = reserve_stock(
                    order_id=order_created.order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                )

                # Emit StockReserved message
                from apps.messaging.messages import StockReserved

                stock_reserved = StockReserved(
                    correlation_id=order_created.correlation_id,
                    causation_id=order_created.correlation_id,
                    timestamp=datetime.now().isoformat(),
                    order_id=order_created.order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    reservation_id=reservation.id,
                )

                create_outbox_message(
                    message_type="StockReserved",
                    payload=stock_reserved.model_dump(mode="json"),
                    aggregate_type="inventory",
                    aggregate_id=reservation.id,
                    correlation_id=order_created.correlation_id,
                    causation_id=order_created.correlation_id,
                )

                logger.info(
                    "Stock reserved successfully",
                    order_id=str(order_created.order_id),
                    product_id=str(item.product_id),
                    quantity=item.quantity,
                    reservation_id=str(reservation.id),
                )

            except Exception as e:
                # Emit StockReservationFailed message
                from apps.messaging.messages import StockReservationFailed

                stock_failed = StockReservationFailed(
                    correlation_id=order_created.correlation_id,
                    causation_id=order_created.correlation_id,
                    timestamp=datetime.now().isoformat(),
                    order_id=order_created.order_id,
                    product_id=item.product_id,
                    requested_quantity=item.quantity,
                    available_quantity=0,  # Would need to fetch actual quantity
                    reason=str(e),
                )

                create_outbox_message(
                    message_type="StockReservationFailed",
                    payload=stock_failed.model_dump(mode="json"),
                    aggregate_type="inventory",
                    aggregate_id=item.product_id,
                    correlation_id=order_created.correlation_id,
                    causation_id=order_created.correlation_id,
                )

                logger.exception(
                    "Failed to reserve stock",
                    order_id=str(order_created.order_id),
                    product_id=str(item.product_id),
                )

    except DuplicateMessageError:
        logger.info(
            "Duplicate message, skipping",
            consumer=consumer,
            correlation_id=str(order_created.correlation_id),
        )
    except Exception as e:
        # Check if should send to DLQ (retry exhausted or broker error)
        if should_send_to_dlq(e):
            handle_dead_letter(
                queue_name="inventory",
                message_type="OrderCreated",
                payload=message,
                error_message=str(e),
                correlation_id=order_created.correlation_id,
                retry_count=3,  # max_retries
            )
            logger.error(
                "Sent to DLQ after retry exhaustion",
                order_id=str(order_created.order_id),
                error=str(e),
            )
            # Reject without requeue to prevent infinite loop
            return
        logger.exception(
            "Failed to handle OrderCreated message",
            order_id=str(order_created.order_id),
        )
        raise
