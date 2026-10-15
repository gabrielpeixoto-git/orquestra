"""Celery beat task for watchdog monitoring of stuck orders."""

from datetime import timedelta

import structlog
from celery import shared_task
from django.utils import timezone

from apps.inventory.models import StockReservation
from apps.inventory.services import release_stock
from apps.messaging.messages import OrderFailed
from apps.orders.models import Order
from apps.orders.services import cancel_order
from apps.outbox.services import create_outbox_message

logger = structlog.get_logger(__name__)

# Timeout threshold for stuck orders (in minutes)
SAGA_TIMEOUT_MINUTES = 30


@shared_task(name="orchestrator.watchdog_saga_timeouts")
def watchdog_saga_timeouts() -> None:
    """Watchdog task to detect and handle stuck orders.

    Checks for orders in PENDING status that have been stuck for longer
    than SAGA_TIMEOUT_MINUTES and triggers compensation.
    """
    timeout_threshold = timezone.now() - timedelta(minutes=SAGA_TIMEOUT_MINUTES)

    stuck_orders = Order.objects.filter(
        status=Order.Status.PENDING,
        created_at__lt=timeout_threshold,
    )

    if not stuck_orders.exists():
        logger.info("No stuck orders found")
        return

    logger.warning(
        "Found stuck orders",
        count=stuck_orders.count(),
        timeout_minutes=SAGA_TIMEOUT_MINUTES,
    )

    for order in stuck_orders:
        try:
            handle_stuck_order(order)
        except Exception:
            logger.exception(
                "Failed to handle stuck order",
                order_id=str(order.id),
            )


def handle_stuck_order(order: Order) -> None:
    """Handle a single stuck order by cancelling and compensating.

    Args:
        order: The stuck order to handle.
    """
    logger.warning(
        "Handling stuck order",
        order_id=str(order.id),
        created_at=order.created_at.isoformat(),
        minutes_stuck=(timezone.now() - order.created_at).total_seconds() / 60,
    )

    # Cancel order
    cancelled_order = cancel_order(order.id)

    # Compensate: release any reserved stock
    reservations = StockReservation.objects.filter(order_id=order.id)
    released_count = 0

    for reservation in reservations:
        try:
            release_stock(reservation.id)
            released_count += 1
            logger.info(
                "Stock released as compensation",
                reservation_id=str(reservation.id),
                order_id=str(order.id),
            )
        except Exception:
            logger.exception(
                "Failed to release stock during compensation",
                reservation_id=str(reservation.id),
                order_id=str(order.id),
            )

    # Emit OrderFailed message
    order_failed = OrderFailed(
        correlation_id=order.id,  # Use order ID as correlation_id for simplicity
        causation_id=order.id,
        timestamp=timezone.now().isoformat(),
        order_id=cancelled_order.id,
        customer_id=cancelled_order.customer_id,
        reason=f"Order stuck in PENDING for more than {SAGA_TIMEOUT_MINUTES} minutes",
        failure_step="watchdog_timeout",
    )

    create_outbox_message(
        message_type="OrderFailed",
        payload=order_failed.model_dump(mode="json"),
        aggregate_type="order",
        aggregate_id=cancelled_order.id,
        correlation_id=order.id,
        causation_id=order.id,
    )

    logger.info(
        "Stuck order handled successfully",
        order_id=str(order.id),
        stock_released=released_count,
    )
