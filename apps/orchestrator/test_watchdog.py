"""Tests for orchestrator watchdog."""

import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.inventory.models import StockReservation
from apps.orchestrator.tasks.watchdog import (
    handle_stuck_order,
    watchdog_saga_timeouts,
)
from apps.orders.models import Order
from apps.orders.services import create_order


@pytest.fixture
def order() -> Order:
    """Create a test order."""
    return create_order(
        customer_id=uuid.uuid4(),
        items=[],
    )


@pytest.mark.django_db
def test_watchdog_no_stuck_orders() -> None:
    """Test watchdog when there are no stuck orders."""
    watchdog_saga_timeouts()
    # Should not raise any errors


@pytest.mark.django_db
def test_watchdog_with_stuck_order(order: Order) -> None:
    """Test watchdog detects and handles stuck orders."""
    # Make the order old enough to be considered stuck
    order.created_at = timezone.now() - timezone.timedelta(minutes=31)
    order.save()

    with patch("apps.orchestrator.tasks.watchdog.handle_stuck_order") as mock_handle:
        watchdog_saga_timeouts()
        mock_handle.assert_called_once()


@pytest.mark.django_db
def test_handle_stuck_order_cancels_order(order: Order) -> None:
    """Test that handle_stuck_order cancels the order."""
    with patch("apps.orchestrator.tasks.watchdog.create_outbox_message") as mock_outbox:
        handle_stuck_order(order)
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED
        mock_outbox.assert_called_once()
        call_args = mock_outbox.call_args
        assert call_args.kwargs["message_type"] == "OrderFailed"


@pytest.mark.django_db
def test_handle_stuck_order_stock_release_error_continues(order: Order) -> None:
    """Test that handle_stuck_order continues even if stock release fails."""
    # Create a stock reservation for the order
    product_id = uuid.uuid4()
    StockReservation.objects.create(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=product_id,
        quantity=10,
        status=StockReservation.Status.ACTIVE,
        expires_at=timezone.now() + timedelta(minutes=30),
    )

    with (
        patch(
            "apps.orchestrator.tasks.watchdog.release_stock", side_effect=Exception("Stock error")
        ),
        patch("apps.orchestrator.tasks.watchdog.create_outbox_message") as mock_outbox,
    ):
        handle_stuck_order(order)
        # Should still cancel order and emit OrderFailed even if stock release fails
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED
        mock_outbox.assert_called_once()


@pytest.mark.django_db
def test_watchdog_handles_one_stuck_order_error_continues(order: Order) -> None:
    """Test that watchdog continues even if one stuck order handling fails."""
    # Make the order old enough to be considered stuck
    order.created_at = timezone.now() - timedelta(minutes=31)
    order.save()

    with patch(
        "apps.orchestrator.tasks.watchdog.handle_stuck_order",
        side_effect=Exception("Handler error"),
    ):
        # Should not raise, just log the error
        watchdog_saga_timeouts()


@pytest.mark.django_db
def test_handle_stuck_order_with_stock_reservation(order: Order) -> None:
    """Test that handle_stuck_order releases stock reservations."""
    from apps.inventory.models import Product

    product_id = uuid.uuid4()
    Product.objects.create(
        id=product_id,
        name="Test Product",
        price=Decimal("10.00"),
        stock_quantity=100,
    )
    reservation = StockReservation.objects.create(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=product_id,
        quantity=10,
        status=StockReservation.Status.ACTIVE,
        expires_at=timezone.now() + timedelta(minutes=30),
    )

    with patch("apps.orchestrator.tasks.watchdog.create_outbox_message") as mock_outbox:
        handle_stuck_order(order)
        reservation.refresh_from_db()
        assert reservation.status == StockReservation.Status.RELEASED
        mock_outbox.assert_called_once()
