"""Services for order management."""

import uuid
from datetime import datetime
from decimal import Decimal

import structlog

from apps.messaging.messages import OrderCreated, OrderItemMessage
from apps.orders.models import Order, OrderItem
from apps.outbox.services import create_outbox_message

logger = structlog.get_logger(__name__)


class OrderCreationError(Exception):
    """Error raised when order creation fails."""


class OrderNotFoundError(Exception):
    """Error raised when order is not found."""


def create_order(
    customer_id: uuid.UUID,
    items: list[dict[str, object]],
) -> Order:
    """Create a new order with items.

    Args:
        customer_id: UUID of the customer.
        items: List of dictionaries containing product_id, quantity, and unit_price.

    Returns:
        The created Order instance.

    Raises:
        OrderCreationError: If order creation fails.
    """
    logger.info("Creating order", customer_id=str(customer_id), items_count=len(items))

    try:
        total_amount = Decimal("0.00")
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=customer_id,
            total_amount=total_amount,
            status=Order.Status.PENDING,
        )

        order_items = []
        for item in items:
            product_id = uuid.UUID(str(item["product_id"]))
            quantity = int(item["quantity"])
            unit_price = Decimal(str(item["unit_price"]))
            total_price = unit_price * quantity
            total_amount += total_price

            order_item = OrderItem.objects.create(
                id=uuid.uuid4(),
                order=order,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            order_items.append(order_item)

        order.total_amount = total_amount
        order.save()

        logger.info(
            "Order created successfully",
            order_id=str(order.id),
            total_amount=str(total_amount),
        )

        # Emit OrderCreated message to outbox
        correlation_id = uuid.uuid4()
        order_items_msg = [
            OrderItemMessage(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in order_items
        ]

        order_created = OrderCreated(
            correlation_id=correlation_id,
            causation_id=None,
            timestamp=datetime.now().isoformat(),
            order_id=order.id,
            customer_id=customer_id,
            total_amount=total_amount,
            items=order_items_msg,
        )

        create_outbox_message(
            message_type="OrderCreated",
            payload=order_created.model_dump(mode="json"),
            aggregate_type="order",
            aggregate_id=order.id,
            correlation_id=correlation_id,
            causation_id=None,
        )

        logger.info(
            "OrderCreated message emitted to outbox",
            order_id=str(order.id),
            correlation_id=str(correlation_id),
        )
    except Exception as e:
        logger.exception("Failed to create order", customer_id=str(customer_id))
        error_msg = f"Failed to create order: {e}"
        raise OrderCreationError(error_msg) from e
    else:
        return order


def cancel_order(order_id: uuid.UUID) -> Order:
    """Cancel an order.

    Args:
        order_id: UUID of the order to cancel.

    Returns:
        The cancelled Order instance.

    Raises:
        OrderNotFoundError: If order does not exist.
    """
    logger.info("Cancelling order", order_id=str(order_id))

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist as e:
        logger.exception("Order not found", order_id=str(order_id))
        error_msg = f"Order {order_id} not found"
        raise OrderNotFoundError(error_msg) from e

    if order.status == Order.Status.CANCELLED:
        logger.warning("Order already cancelled", order_id=str(order_id))
        return order

    order.status = Order.Status.CANCELLED
    order.save()

    logger.info("Order cancelled successfully", order_id=str(order_id))
    return order


def update_order_status(order_id: uuid.UUID, status: str) -> Order:
    """Update the status of an order.

    Args:
        order_id: UUID of the order.
        status: New status value.

    Returns:
        The updated Order instance.

    Raises:
        OrderNotFoundError: If order does not exist.
    """
    logger.info("Updating order status", order_id=str(order_id), status=status)

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist as e:
        logger.exception("Order not found", order_id=str(order_id))
        error_msg = f"Order {order_id} not found"
        raise OrderNotFoundError(error_msg) from e

    order.status = status
    order.save()

    logger.info("Order status updated", order_id=str(order_id), status=status)
    return order


def get_order(order_id: uuid.UUID) -> Order:
    """Get an order by ID.

    Args:
        order_id: UUID of the order.

    Returns:
        The Order instance.

    Raises:
        OrderNotFoundError: If order does not exist.
    """
    try:
        return Order.objects.get(id=order_id)
    except Order.DoesNotExist as e:
        logger.exception("Order not found", order_id=str(order_id))
        error_msg = f"Order {order_id} not found"
        raise OrderNotFoundError(error_msg) from e
