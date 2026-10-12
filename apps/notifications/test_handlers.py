"""Tests for notifications handlers."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.notifications.tasks.handlers import (
    handle_payment_failed,
    handle_payment_processed,
)


@pytest.mark.django_db
def test_handle_payment_processed_success() -> None:
    """Test successful handling of PaymentProcessed message."""
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    with (
        patch("apps.notifications.tasks.handlers.send_notification") as mock_send,
        patch("apps.notifications.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        notification = MagicMock()
        notification.id = uuid.uuid4()
        notification.recipient = "customer@example.com"
        notification.type = "EMAIL"
        notification.subject = "Payment Successful"
        mock_send.return_value = notification
        handle_payment_processed(message)
        mock_outbox.assert_called_once()


@pytest.mark.django_db
def test_handle_payment_processed_idempotent() -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    # First call
    handle_payment_processed(message)

    # Second call (should be idempotent)
    with patch("apps.notifications.tasks.handlers.create_outbox_message") as mock_outbox:
        handle_payment_processed(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_payment_processed_duplicate_message() -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError

    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    with (
        patch(
            "apps.notifications.tasks.handlers.process_message", side_effect=DuplicateMessageError()
        ),
        patch("apps.notifications.tasks.handlers.create_outbox_message") as mock_outbox,
    ):
        handle_payment_processed(message)
        mock_outbox.assert_not_called()


@pytest.mark.django_db
def test_handle_payment_processed_send_to_dlq() -> None:
    """Test that messages are sent to DLQ when retry is exhausted."""
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "payment_id": str(uuid.uuid4()),
        "amount": 100.00,
        "gateway_transaction_id": "txn_123",
    }

    with (
        patch(
            "apps.notifications.tasks.handlers.send_notification",
            side_effect=Exception("Notification failed"),
        ),
        patch("apps.notifications.tasks.handlers.should_send_to_dlq", return_value=True),
        patch("apps.notifications.tasks.handlers.handle_dead_letter") as mock_handle_dlq,
    ):
        handle_payment_processed(message)
        mock_handle_dlq.assert_called_once()
        call_args = mock_handle_dlq.call_args
        assert call_args.kwargs["queue_name"] == "notifications"
        assert call_args.kwargs["message_type"] == "PaymentProcessed"


@pytest.mark.django_db
def test_handle_payment_failed_success() -> None:
    """Test successful handling of PaymentFailed message."""
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with patch("apps.notifications.tasks.handlers.send_notification") as mock_send:
        handle_payment_failed(message)

        # Check that notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert "Payment Failed" in call_args.kwargs["subject"]


@pytest.mark.django_db
def test_handle_payment_failed_idempotent() -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    # First call
    handle_payment_failed(message)

    # Second call (should be idempotent)
    with patch("apps.notifications.tasks.handlers.send_notification") as mock_send:
        handle_payment_failed(message)
        mock_send.assert_not_called()


@pytest.mark.django_db
def test_handle_payment_failed_duplicate_message() -> None:
    """Test handling when DuplicateMessageError is raised."""
    from apps.inbox.services import DuplicateMessageError

    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with (
        patch(
            "apps.notifications.tasks.handlers.process_message", side_effect=DuplicateMessageError()
        ),
        patch("apps.notifications.tasks.handlers.send_notification") as mock_send,
    ):
        handle_payment_failed(message)
        mock_send.assert_not_called()


@pytest.mark.django_db
def test_handle_payment_failed_send_to_dlq() -> None:
    """Test that messages are sent to DLQ when retry is exhausted."""
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(order_id),
        "amount": 100.00,
        "reason": "Insufficient funds",
    }

    with (
        patch(
            "apps.notifications.tasks.handlers.send_notification",
            side_effect=Exception("Notification failed"),
        ),
        patch("apps.notifications.tasks.handlers.should_send_to_dlq", return_value=True),
        patch("apps.notifications.tasks.handlers.handle_dead_letter") as mock_handle_dlq,
    ):
        handle_payment_failed(message)
        mock_handle_dlq.assert_called_once()
        call_args = mock_handle_dlq.call_args
        assert call_args.kwargs["queue_name"] == "notifications"
        assert call_args.kwargs["message_type"] == "PaymentFailed"
