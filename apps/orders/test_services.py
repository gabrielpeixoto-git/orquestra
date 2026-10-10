"""Tests for order services."""

import uuid
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.orders.models import Order
from apps.orders.services import (
    OrderCreationError,
    OrderNotFoundError,
    cancel_order,
    create_order,
    get_order,
    update_order_status,
)


class CreateOrderTests(TestCase):
    """Tests for create_order service."""

    def test_create_order_with_single_item(self) -> None:
        """Test creating an order with a single item."""
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": uuid.uuid4(),
                "quantity": 2,
                "unit_price": Decimal("10.50"),
            }
        ]

        order = create_order(customer_id, items)

        assert order.customer_id == customer_id
        assert order.status == Order.Status.PENDING
        assert order.total_amount == Decimal("21.00")
        assert order.items.count() == 1

    def test_create_order_with_multiple_items(self) -> None:
        """Test creating an order with multiple items."""
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": uuid.uuid4(),
                "quantity": 2,
                "unit_price": Decimal("10.00"),
            },
            {
                "product_id": uuid.uuid4(),
                "quantity": 1,
                "unit_price": Decimal("5.00"),
            },
        ]

        order = create_order(customer_id, items)

        assert order.customer_id == customer_id
        assert order.total_amount == Decimal("25.00")
        assert order.items.count() == 2

    def test_create_order_calculates_total_correctly(self) -> None:
        """Test that order total is calculated correctly."""
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": uuid.uuid4(),
                "quantity": 3,
                "unit_price": Decimal("7.50"),
            }
        ]

        order = create_order(customer_id, items)

        assert order.total_amount == Decimal("22.50")

    def test_create_order_with_invalid_data_raises_error(self) -> None:
        """Test that creating order with invalid data raises error."""
        customer_id = uuid.uuid4()
        items = [{"invalid": "data"}]

        with pytest.raises(OrderCreationError):
            create_order(customer_id, items)


class CancelOrderTests(TestCase):
    """Tests for cancel_order service."""

    def test_cancel_pending_order(self) -> None:
        """Test cancelling a pending order."""
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            total_amount=Decimal("100.00"),
            status=Order.Status.PENDING,
        )

        cancelled_order = cancel_order(order.id)

        assert cancelled_order.status == Order.Status.CANCELLED

    def test_cancel_already_cancelled_order(self) -> None:
        """Test cancelling an already cancelled order is idempotent."""
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            total_amount=Decimal("100.00"),
            status=Order.Status.CANCELLED,
        )

        cancelled_order = cancel_order(order.id)

        assert cancelled_order.status == Order.Status.CANCELLED

    def test_cancel_nonexistent_order_raises_error(self) -> None:
        """Test cancelling a non-existent order raises error."""
        order_id = uuid.uuid4()

        with pytest.raises(OrderNotFoundError):
            cancel_order(order_id)


class UpdateOrderStatusTests(TestCase):
    """Tests for update_order_status service."""

    def test_update_order_status(self) -> None:
        """Test updating order status."""
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            total_amount=Decimal("100.00"),
            status=Order.Status.PENDING,
        )

        updated_order = update_order_status(order.id, Order.Status.CONFIRMED)

        assert updated_order.status == Order.Status.CONFIRMED

    def test_update_nonexistent_order_status_raises_error(self) -> None:
        """Test updating status of non-existent order raises error."""
        order_id = uuid.uuid4()

        with pytest.raises(OrderNotFoundError):
            update_order_status(order_id, Order.Status.CONFIRMED)


class GetOrderTests(TestCase):
    """Tests for get_order service."""

    def test_get_existing_order(self) -> None:
        """Test getting an existing order."""
        order_id = uuid.uuid4()
        Order.objects.create(
            id=order_id,
            customer_id=uuid.uuid4(),
            total_amount=Decimal("100.00"),
            status=Order.Status.PENDING,
        )

        order = get_order(order_id)

        assert order.id == order_id

    def test_get_nonexistent_order_raises_error(self) -> None:
        """Test getting a non-existent order raises error."""
        order_id = uuid.uuid4()

        with pytest.raises(OrderNotFoundError):
            get_order(order_id)
