"""Tests for orchestrator watchdog."""

import uuid

import pytest

from apps.orchestrator.tasks.watchdog import (
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
