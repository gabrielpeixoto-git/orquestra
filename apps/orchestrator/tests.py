"""Tests for orchestrator services and tasks."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.inventory.models import StockReservation
from apps.inventory.services import create_product, reserve_stock
from apps.orchestrator.tasks.watchdog import (
    SAGA_TIMEOUT_MINUTES,
    handle_stuck_order,
    watchdog_saga_timeouts,
)
from apps.orders.models import Order
from apps.orders.services import create_order


@pytest.mark.usefixtures("db")
def test_watchdog_no_stuck_orders() -> None:
    """Test watchdog when there are no stuck orders."""
    # Create a recent order (not stuck)
    product = create_product(
        name="Test Product",
        description="Test description",
        price=Decimal("10.00"),
        stock_quantity=100,
    )

    create_order(
        customer_id=uuid4(),
        items=[{"product_id": product.id, "quantity": 2, "unit_price": "10.00"}],
    )

    # Run watchdog
    watchdog_saga_timeouts()

    # Order should still be PENDING
    orders = Order.objects.filter(status=Order.Status.PENDING)
    assert orders.count() == 1


@pytest.mark.usefixtures("db")
def test_watchdog_detects_stuck_orders() -> None:
    """Test watchdog detects and handles stuck orders."""
    # Create a product
    product = create_product(
        name="Test Product",
        description="Test description",
        price=Decimal("10.00"),
        stock_quantity=100,
    )

    # Create an order
    order = create_order(
        customer_id=uuid4(),
        items=[{"product_id": product.id, "quantity": 2, "unit_price": "10.00"}],
    )

    # Reserve stock
    reserve_stock(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
    )

    # Manually set created_at to make it appear stuck
    timeout_threshold = timezone.now() - timedelta(minutes=SAGA_TIMEOUT_MINUTES + 1)
    order.created_at = timeout_threshold
    order.save()

    # Run watchdog
    watchdog_saga_timeouts()

    # Order should be cancelled
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED

    # Stock should be released (status = RELEASED)
    reservations = StockReservation.objects.filter(order_id=order.id)
    assert reservations.count() == 1
    assert reservations.first().status == StockReservation.Status.RELEASED


@pytest.mark.usefixtures("db")
def test_handle_stuck_order_with_stock_reservation() -> None:
    """Test handling a stuck order with stock reservations."""
    # Create a product
    product = create_product(
        name="Test Product",
        description="Test description",
        price=Decimal("10.00"),
        stock_quantity=100,
    )

    # Create an order
    order = create_order(
        customer_id=uuid4(),
        items=[{"product_id": product.id, "quantity": 2, "unit_price": "10.00"}],
    )

    # Reserve stock
    reserve_stock(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
    )

    # Make order appear stuck
    timeout_threshold = timezone.now() - timedelta(minutes=SAGA_TIMEOUT_MINUTES + 1)
    order.created_at = timeout_threshold
    order.save()

    # Handle stuck order
    handle_stuck_order(order)

    # Order should be cancelled
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED

    # Stock should be released (status = RELEASED)
    reservations = StockReservation.objects.filter(order_id=order.id)
    assert reservations.count() == 1
    assert reservations.first().status == StockReservation.Status.RELEASED


@pytest.mark.usefixtures("db")
def test_handle_stuck_order_without_stock_reservation() -> None:
    """Test handling a stuck order without stock reservations."""
    # Create a product
    product = create_product(
        name="Test Product",
        description="Test description",
        price=Decimal("10.00"),
        stock_quantity=100,
    )

    # Create an order
    order = create_order(
        customer_id=uuid4(),
        items=[{"product_id": product.id, "quantity": 2, "unit_price": "10.00"}],
    )

    # Make order appear stuck
    timeout_threshold = timezone.now() - timedelta(minutes=SAGA_TIMEOUT_MINUTES + 1)
    order.created_at = timeout_threshold
    order.save()

    # Handle stuck order
    handle_stuck_order(order)

    # Order should be cancelled
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED


@pytest.mark.usefixtures("db")
def test_watchdog_handles_multiple_stuck_orders() -> None:
    """Test watchdog handles multiple stuck orders."""
    # Create a product
    product = create_product(
        name="Test Product",
        description="Test description",
        price=Decimal("10.00"),
        stock_quantity=100,
    )

    # Create multiple stuck orders
    timeout_threshold = timezone.now() - timedelta(minutes=SAGA_TIMEOUT_MINUTES + 1)

    for _ in range(3):
        order = create_order(
            customer_id=uuid4(),
            items=[{"product_id": product.id, "quantity": 2, "unit_price": "10.00"}],
        )
        order.created_at = timeout_threshold
        order.save()

    # Create a recent order (not stuck)
    create_order(
        customer_id=uuid4(),
        items=[{"product_id": product.id, "quantity": 2, "unit_price": "10.00"}],
    )

    # Run watchdog
    watchdog_saga_timeouts()

    # All stuck orders should be cancelled
    cancelled_orders = Order.objects.filter(status=Order.Status.CANCELLED)
    assert cancelled_orders.count() == 3

    # Recent order should still be PENDING
    pending_orders = Order.objects.filter(status=Order.Status.PENDING)
    assert pending_orders.count() == 1
