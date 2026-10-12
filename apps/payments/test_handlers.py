"""Tests for payments handlers."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.payments.tasks.handlers import handle_stock_reserved


@pytest.mark.django_db
def test_handle_stock_reserved_order_not_found() -> None:
    """Test handling when order does not exist."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(uuid.uuid4()),  # Non-existent order
        "product_id": str(uuid.uuid4()),
        "quantity": 1,
        "reservation_id": str(uuid.uuid4()),
    }

    with patch("apps.payments.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_stock_reserved(message)

        # Should not create outbox message if order not found
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_stock_reserved_success() -> None:
    """Test successful handling of StockReserved message."""
    from apps.orders.services import create_order

    order = create_order(
        customer_id=uuid.uuid4(),
        items=[],
    )

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "quantity": 1,
        "reservation_id": str(uuid.uuid4()),
    }

    with (
        patch("apps.payments.tasks.handlers.process_payment") as mock_process,
        patch("apps.payments.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        mock_process.return_value = MagicMock(id=uuid.uuid4())
        handle_stock_reserved(message)
        mock_outbox.assert_called_once()


@pytest.mark.django_db
def test_handle_stock_reserved_payment_failure() -> None:
    """Test handling when payment fails."""
    from apps.orders.services import create_order

    order = create_order(
        customer_id=uuid.uuid4(),
        items=[],
    )

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "quantity": 1,
        "reservation_id": str(uuid.uuid4()),
    }

    with (
        patch(
            "apps.payments.tasks.handlers.process_payment",
            side_effect=Exception("Payment declined"),
        ),
        patch("apps.payments.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_stock_reserved(message)
        mock_outbox.assert_called_once()
        call_args = mock_outbox.call_args
        assert call_args.kwargs["message_type"] == "PaymentFailed"


@pytest.mark.django_db
def test_handle_stock_reserved_duplicate_message() -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError
    from apps.orders.services import create_order

    order = create_order(
        customer_id=uuid.uuid4(),
        items=[],
    )

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "quantity": 1,
        "reservation_id": str(uuid.uuid4()),
    }

    with (
        patch("apps.payments.tasks.handlers.process_message", side_effect=DuplicateMessageError()),
        patch("apps.payments.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_stock_reserved(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_stock_reserved_idempotent() -> None:
    """Test that duplicate messages are skipped."""
    from apps.orders.services import create_order

    order = create_order(
        customer_id=uuid.uuid4(),
        items=[],
    )

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "quantity": 1,
        "reservation_id": str(uuid.uuid4()),
    }

    # First call
    handle_stock_reserved(message)

    # Second call (should be idempotent)
    with patch("apps.payments.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_stock_reserved(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_stock_reserved_raises_on_exception() -> None:
    """Test StockReserved raises on non-DLQ exception."""
    from apps.orders.services import create_order

    order = create_order(
        customer_id=uuid.uuid4(),
        items=[],
    )

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "quantity": 1,
        "reservation_id": str(uuid.uuid4()),
    }

    with (
        patch("apps.payments.tasks.handlers.should_send_to_dlq", return_value=False),
        patch("apps.payments.tasks.handlers.process_message", side_effect=Exception("DB error")),
        pytest.raises(Exception, match="DB error"),
    ):
        handle_stock_reserved(message)
