"""Tests for relay management command."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from apps.outbox.models import OutboxMessage
from apps.outbox.services import create_outbox_message


@pytest.fixture
def outbox_message() -> OutboxMessage:
    """Create a test outbox message."""
    correlation_id = uuid.uuid4()
    payload = {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "timestamp": datetime.now().isoformat(),
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "items": [],
        "total_amount": 100.00,
    }
    return create_outbox_message(
        message_type="OrderCreated",
        payload=payload,
        aggregate_type="order",
        aggregate_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        causation_id=correlation_id,
    )


@pytest.mark.django_db
def test_relay_command_no_messages() -> None:
    """Test relay command when there are no pending messages."""
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("relay", "--limit", 10)

        # Should not publish any messages
        mock_channel.basic_publish.assert_not_called()


@pytest.mark.django_db
def test_relay_command_success(outbox_message: OutboxMessage) -> None:
    """Test successful relay of messages."""
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("relay", "--limit", 10)

        # Should publish the message
        assert mock_channel.basic_publish.call_count == 1

        # Check that message was marked as published
        outbox_message.refresh_from_db()
        assert outbox_message.status == OutboxMessage.Status.PUBLISHED


@pytest.mark.django_db
def test_relay_command_unknown_message_type() -> None:
    """Test relay command with unknown message type."""
    correlation_id = uuid.uuid4()
    payload = {"test": "data"}
    message = create_outbox_message(
        message_type="UnknownType",
        payload=payload,
        aggregate_type="test",
        aggregate_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        causation_id=correlation_id,
    )

    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("relay", "--limit", 10)

        # Should not publish unknown message type
        mock_channel.basic_publish.assert_not_called()

        # Should mark as failed
        message.refresh_from_db()
        assert message.status == OutboxMessage.Status.FAILED


@pytest.mark.django_db
def test_relay_command_connection_error() -> None:
    """Test relay command handles connection errors."""
    with (
        patch("pika.BlockingConnection", side_effect=ConnectionError("Connection failed")),
        pytest.raises(ConnectionError),
    ):
        call_command("relay", "--limit", 10)


@pytest.mark.django_db
def test_relay_command_publish_error(outbox_message: OutboxMessage) -> None:
    """Test relay command handles publish errors."""
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_channel.basic_publish.side_effect = Exception("Publish failed")
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("relay", "--limit", 10)

        # Should mark message as failed
        outbox_message.refresh_from_db()
        assert outbox_message.status == OutboxMessage.Status.FAILED


@pytest.mark.django_db
def test_relay_command_custom_limit() -> None:
    """Test relay command with custom limit."""
    # Create 5 pending messages
    for _i in range(5):
        correlation_id = uuid.uuid4()
        payload = {
            "correlation_id": str(correlation_id),
            "causation_id": str(correlation_id),
            "timestamp": datetime.now().isoformat(),
            "order_id": str(uuid.uuid4()),
            "customer_id": str(uuid.uuid4()),
            "items": [],
            "total_amount": 100.00,
        }
        create_outbox_message(
            message_type="OrderCreated",
            payload=payload,
            aggregate_type="order",
            aggregate_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            causation_id=correlation_id,
        )

    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("relay", "--limit", 3)

        # Should only publish 3 messages
        assert mock_channel.basic_publish.call_count == 3


@pytest.mark.django_db
def test_relay_command_deserialize_error_marks_failed() -> None:
    """Test relay command marks message as failed on deserialize error."""
    correlation_id = uuid.uuid4()
    message = create_outbox_message(
        message_type="OrderCreated",
        payload={"invalid": "payload"},  # Invalid payload
        aggregate_type="order",
        aggregate_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        causation_id=correlation_id,
    )

    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("relay", "--limit", 10)

        # Should mark message as failed
        message.refresh_from_db()
        assert message.status == OutboxMessage.Status.FAILED


@pytest.mark.django_db
def test_relay_unknown_message_type() -> None:
    """Test relay command with unknown message type."""
    from apps.outbox.management.commands.relay import Command
    from apps.outbox.models import OutboxMessage

    message = OutboxMessage.objects.create(
        message_type="UnknownMessage",
        payload={"test": "data"},
        aggregate_type="test",
        aggregate_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        status=OutboxMessage.Status.PENDING,
    )

    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        command = Command()
        command.handle(limit=100, rabbitmq_url="amqp://localhost")

        # Should mark message as failed due to unknown type
        message.refresh_from_db()
        assert message.status == OutboxMessage.Status.FAILED


@pytest.mark.django_db
def test_relay_with_custom_limit() -> None:
    """Test relay command with custom limit."""
    from apps.outbox.management.commands.relay import Command
    from apps.outbox.models import OutboxMessage

    # Create 5 messages
    for _ in range(5):
        OutboxMessage.objects.create(
            message_type="OrderCreated",
            payload={"test": "data"},
            aggregate_type="order",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            status=OutboxMessage.Status.PENDING,
        )

    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        command = Command()
        command.handle(limit=3, rabbitmq_url="amqp://localhost")

        # Should only process 3 messages
        pending_count = OutboxMessage.objects.filter(status=OutboxMessage.Status.PENDING).count()
        assert pending_count == 2
