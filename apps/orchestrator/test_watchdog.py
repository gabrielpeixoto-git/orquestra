"""Tests for orchestrator watchdog."""

import uuid
from unittest.mock import patch

import pytest
from django.utils import timezone

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
