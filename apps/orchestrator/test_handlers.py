"""Tests for orchestrator handlers."""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from apps.orchestrator.tasks.handlers import (
    handle_payment_failed,
    handle_payment_processed,
    handle_stock_reservation_failed,
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
def test_handle_payment_processed_idempotent(order: Order) -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    # First call
    handle_payment_processed(message)

    # Second call (should be idempotent)
    with patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_payment_processed(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_payment_processed_success(order: Order) -> None:
    """Test successful handling of PaymentProcessed message."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    with patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_payment_processed(message)
        mock_outbox.assert_called_once()
        call_args = mock_outbox.call_args
        assert call_args.kwargs["message_type"] == "OrderConfirmed"


@pytest.mark.django_db
def test_handle_payment_processed_duplicate_message(order: Order) -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    with (
        patch(
            "apps.orchestrator.tasks.handlers.process_message", side_effect=DuplicateMessageError()
        ),
        patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_payment_processed(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_payment_failed_idempotent(order: Order) -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    # First call
    handle_payment_failed(message)

    # Second call (should be idempotent)
    with patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_payment_failed(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_payment_failed_success(order: Order) -> None:
    """Test successful handling of PaymentFailed message."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_payment_failed(message)
        mock_outbox.assert_called_once()
        call_args = mock_outbox.call_args
        assert call_args.kwargs["message_type"] == "OrderFailed"


@pytest.mark.django_db
def test_handle_payment_failed_duplicate_message(order: Order) -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with (
        patch(
            "apps.orchestrator.tasks.handlers.process_message", side_effect=DuplicateMessageError()
        ),
        patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_payment_failed(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_stock_reservation_failed_idempotent(order: Order) -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "requested_quantity": 10,
        "available_quantity": 5,
        "reason": "Insufficient stock",
    }

    # First call
    handle_stock_reservation_failed(message)

    # Second call (should be idempotent)
    with patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_stock_reservation_failed(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_stock_reservation_failed_success(order: Order) -> None:
    """Test successful handling of StockReservationFailed message."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "requested_quantity": 10,
        "available_quantity": 5,
        "reason": "Insufficient stock",
    }

    with patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_stock_reservation_failed(message)
        mock_outbox.assert_called_once()
        call_args = mock_outbox.call_args
        assert call_args.kwargs["message_type"] == "OrderFailed"


@pytest.mark.django_db
def test_handle_stock_reservation_failed_duplicate_message(order: Order) -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "requested_quantity": 10,
        "available_quantity": 5,
        "reason": "Insufficient stock",
    }

    with (
        patch(
            "apps.orchestrator.tasks.handlers.process_message", side_effect=DuplicateMessageError()
        ),
        patch("apps.orchestrator.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_stock_reservation_failed(message)
        mock_outbox.assert_not_called()
