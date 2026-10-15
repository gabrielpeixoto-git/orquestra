"""Tests for orchestrator handlers."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
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
        "timestamp": datetime.now(UTC).isoformat(),
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
        "timestamp": datetime.now(UTC).isoformat(),
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
        "timestamp": datetime.now(UTC).isoformat(),
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
def test_handle_payment_processed_creates_order_confirmed_message(order: Order) -> None:
    """Test that OrderConfirmed message is created with correct payload."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
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
        assert call_args.kwargs["aggregate_type"] == "order"
        assert call_args.kwargs["aggregate_id"] == order.id


@pytest.mark.django_db
def test_handle_payment_failed_idempotent(order: Order) -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
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
        "timestamp": datetime.now(UTC).isoformat(),
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
        "timestamp": datetime.now(UTC).isoformat(),
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
def test_handle_payment_failed_with_stock_compensation(order: Order) -> None:
    """Test handling payment failed with stock compensation."""
    from apps.inventory.models import Product, StockReservation

    correlation_id = uuid.uuid4()
    product_id = uuid.uuid4()

    # Create product and stock reservation for the order
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
        expires_at=datetime.now(UTC),
    )

    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    handle_payment_failed(message)

    # Verify stock was released (status changed to RELEASED)
    reservation.refresh_from_db()
    assert reservation.status == StockReservation.Status.RELEASED


@pytest.mark.django_db
def test_handle_payment_failed_with_multiple_reservations(order: Order) -> None:
    """Test handling payment failed with multiple stock reservations."""
    from apps.inventory.models import Product, StockReservation

    correlation_id = uuid.uuid4()
    product_id1 = uuid.uuid4()
    product_id2 = uuid.uuid4()

    # Create products and stock reservations for the order
    Product.objects.create(
        id=product_id1,
        name="Test Product 1",
        price=Decimal("10.00"),
        stock_quantity=100,
    )
    Product.objects.create(
        id=product_id2,
        name="Test Product 2",
        price=Decimal("20.00"),
        stock_quantity=50,
    )
    StockReservation.objects.create(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=product_id1,
        quantity=5,
        expires_at=datetime.now(UTC),
    )
    StockReservation.objects.create(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=product_id2,
        quantity=3,
        expires_at=datetime.now(UTC),
    )

    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    handle_payment_failed(message)

    # Verify both stocks were released
    reservations = StockReservation.objects.filter(order_id=order.id)
    for reservation in reservations:
        assert reservation.status == StockReservation.Status.RELEASED


@pytest.mark.django_db
def test_handle_payment_failed_with_release_error_continues(order: Order) -> None:
    """Test handling payment failed continues even if one stock release fails."""
    from apps.inventory.models import Product, StockReservation

    correlation_id = uuid.uuid4()
    product_id1 = uuid.uuid4()
    product_id2 = uuid.uuid4()

    # Create products and stock reservations for the order
    Product.objects.create(
        id=product_id1,
        name="Test Product 1",
        price=Decimal("10.00"),
        stock_quantity=100,
    )
    Product.objects.create(
        id=product_id2,
        name="Test Product 2",
        price=Decimal("20.00"),
        stock_quantity=50,
    )
    StockReservation.objects.create(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=product_id1,
        quantity=5,
        expires_at=datetime.now(UTC),
    )
    StockReservation.objects.create(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=product_id2,
        quantity=3,
        expires_at=datetime.now(UTC),
    )

    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with patch(
        "apps.orchestrator.tasks.handlers.release_stock", side_effect=Exception("Release error")
    ):
        handle_payment_failed(message)

    # Verify order was still cancelled even though stock release failed
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED


@pytest.mark.django_db
def test_handle_stock_reservation_failed_idempotent(order: Order) -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
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
        "timestamp": datetime.now(UTC).isoformat(),
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
def test_handle_stock_reservation_failed_creates_order_failed_message(order: Order) -> None:
    """Test that OrderFailed message is created with correct payload."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
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
        assert call_args.kwargs["aggregate_type"] == "order"
        assert call_args.kwargs["aggregate_id"] == order.id


@pytest.mark.django_db
def test_handle_stock_reservation_failed_duplicate_message(order: Order) -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError

    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
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


@pytest.mark.django_db
def test_handle_payment_processed_raises_on_exception(order: Order) -> None:
    """Test PaymentProcessed raises on non-DLQ exception."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    with (
        patch("apps.orchestrator.tasks.handlers.should_send_to_dlq", return_value=False),
        patch(
            "apps.orchestrator.tasks.handlers.update_order_status",
            side_effect=Exception("DB error"),
        ),
        pytest.raises(Exception, match="DB error"),
    ):
        handle_payment_processed(message)


@pytest.mark.django_db
def test_handle_payment_failed_raises_on_exception(order: Order) -> None:
    """Test PaymentFailed raises on non-DLQ exception."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with (
        patch("apps.orchestrator.tasks.handlers.should_send_to_dlq", return_value=False),
        patch("apps.orchestrator.tasks.handlers.cancel_order", side_effect=Exception("DB error")),
        pytest.raises(Exception, match="DB error"),
    ):
        handle_payment_failed(message)


@pytest.mark.django_db
def test_handle_stock_reservation_failed_raises_on_exception(order: Order) -> None:
    """Test StockReservationFailed raises on non-DLQ exception."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "requested_quantity": 10,
        "available_quantity": 5,
        "reason": "Insufficient stock",
    }

    with (
        patch("apps.orchestrator.tasks.handlers.should_send_to_dlq", return_value=False),
        patch("apps.orchestrator.tasks.handlers.cancel_order", side_effect=Exception("DB error")),
        pytest.raises(Exception, match="DB error"),
    ):
        handle_stock_reservation_failed(message)


@pytest.mark.django_db
def test_handle_payment_processed_send_to_dlq(order: Order) -> None:
    """Test PaymentProcessed sends to DLQ on retry exhaustion."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    with (
        patch("apps.orchestrator.tasks.handlers.should_send_to_dlq", return_value=True),
        patch("apps.orchestrator.tasks.handlers.handle_dead_letter") as mock_handle_dlq,
        patch(
            "apps.orchestrator.tasks.handlers.update_order_status",
            side_effect=Exception("DB error"),
        ),
    ):
        handle_payment_processed(message)
        mock_handle_dlq.assert_called_once()
        call_args = mock_handle_dlq.call_args
        assert call_args.kwargs["queue_name"] == "orchestrator"
        assert call_args.kwargs["message_type"] == "PaymentProcessed"


@pytest.mark.django_db
def test_handle_payment_failed_send_to_dlq(order: Order) -> None:
    """Test PaymentFailed sends to DLQ on retry exhaustion."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with (
        patch("apps.orchestrator.tasks.handlers.should_send_to_dlq", return_value=True),
        patch("apps.orchestrator.tasks.handlers.handle_dead_letter") as mock_handle_dlq,
        patch("apps.orchestrator.tasks.handlers.cancel_order", side_effect=Exception("DB error")),
    ):
        handle_payment_failed(message)
        mock_handle_dlq.assert_called_once()
        call_args = mock_handle_dlq.call_args
        assert call_args.kwargs["queue_name"] == "orchestrator"
        assert call_args.kwargs["message_type"] == "PaymentFailed"


@pytest.mark.django_db
def test_handle_stock_reservation_failed_send_to_dlq(order: Order) -> None:
    """Test StockReservationFailed sends to DLQ on retry exhaustion."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "order_id": str(order.id),
        "product_id": str(uuid.uuid4()),
        "requested_quantity": 10,
        "available_quantity": 5,
        "reason": "Insufficient stock",
    }

    with (
        patch("apps.orchestrator.tasks.handlers.should_send_to_dlq", return_value=True),
        patch("apps.orchestrator.tasks.handlers.handle_dead_letter") as mock_handle_dlq,
        patch("apps.orchestrator.tasks.handlers.cancel_order", side_effect=Exception("DB error")),
    ):
        handle_stock_reservation_failed(message)
        mock_handle_dlq.assert_called_once()
        call_args = mock_handle_dlq.call_args
        assert call_args.kwargs["queue_name"] == "orchestrator"
        assert call_args.kwargs["message_type"] == "StockReservationFailed"
