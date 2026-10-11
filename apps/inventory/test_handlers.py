"""Tests for inventory handlers."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.inventory.tasks.handlers import handle_order_created


@pytest.mark.django_db
def test_handle_order_created_idempotent() -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "items": [],
        "total_amount": 200.00,
    }

    # First call
    handle_order_created(message)

    # Second call (should be idempotent)
    with patch("apps.inventory.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_order_created(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_order_created_duplicate_message() -> None:
    """Test that duplicate messages are skipped with DuplicateMessageError."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "items": [],
        "total_amount": 200.00,
    }

    with (
        patch("apps.inventory.tasks.handlers.is_message_processed", return_value=True),
        patch("apps.inventory.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_order_created(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_order_created_success() -> None:
    """Test successful handling of OrderCreated message."""
    correlation_id = uuid.uuid4()
    product_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(product_id),
                "quantity": 2,
                "unit_price": 100.00,
            }
        ],
        "total_amount": 200.00,
    }

    with (
        patch("apps.inventory.tasks.handlers.reserve_stock") as mock_reserve,
        patch("apps.inventory.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        mock_reserve.return_value = MagicMock(id=uuid.uuid4())
        handle_order_created(message)
        mock_outbox.assert_called_once()


@pytest.mark.django_db
def test_handle_order_created_stock_reservation_failure() -> None:
    """Test handling when stock reservation fails."""
    correlation_id = uuid.uuid4()
    product_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(product_id),
                "quantity": 20,
                "unit_price": 100.00,
            }
        ],
        "total_amount": 2000.00,
    }

    with (
        patch(
            "apps.inventory.tasks.handlers.reserve_stock",
            side_effect=Exception("Insufficient stock"),
        ),
        patch("apps.inventory.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_order_created(message)
        mock_outbox.assert_called_once()
        call_args = mock_outbox.call_args
        assert call_args.kwargs["message_type"] == "StockReservationFailed"


@pytest.mark.django_db
def test_handle_order_created_duplicate_message_error() -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "items": [],
        "total_amount": 200.00,
    }

    with (
        patch("apps.inventory.tasks.handlers.process_message", side_effect=DuplicateMessageError()),
        patch("apps.inventory.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_order_created(message)
        mock_outbox.assert_not_called()
