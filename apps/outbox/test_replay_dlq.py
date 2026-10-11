"""Tests for replay_dlq management command."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from apps.outbox.models import DeadLetterMessage
from apps.outbox.services_deadletter import create_dead_letter


@pytest.fixture
def dead_letter() -> DeadLetterMessage:
    """Create a test dead letter message."""
    correlation_id = uuid.uuid4()
    payload = {
        "correlation_id": str(correlation_id),
        "test": "data",
    }
    return create_dead_letter(
        queue_name="inventory",
        message_type="OrderCreated",
        payload=payload,
        error_message="Test error",
        correlation_id=correlation_id,
        retry_count=3,
    )


@pytest.mark.django_db
def test_replay_dlq_command_no_messages() -> None:
    """Test replay command when there are no pending messages."""
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("replay_dlq", "--limit", 10)

        # Should not publish any messages
        mock_channel.basic_publish.assert_not_called()


@pytest.mark.django_db
def test_replay_dlq_command_success(dead_letter: DeadLetterMessage) -> None:
    """Test successful replay of dead letter messages."""
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("replay_dlq", "--limit", 10)

        # Should publish the message
        assert mock_channel.basic_publish.call_count == 1

        # Check that message was marked as replayed
        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.REPLAYED


@pytest.mark.django_db
def test_replay_dlq_command_connection_error() -> None:
    """Test replay command handles connection errors."""
    with (
        patch("pika.BlockingConnection", side_effect=ConnectionError("Connection failed")),
        pytest.raises(ConnectionError),
    ):
        call_command("replay_dlq", "--limit", 10)


@pytest.mark.django_db
def test_replay_dlq_command_publish_error(dead_letter: DeadLetterMessage) -> None:
    """Test replay command handles publish errors."""
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_channel.basic_publish.side_effect = Exception("Publish failed")
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("replay_dlq", "--limit", 10)

        # Should not mark as replayed if publish fails
        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.PENDING


@pytest.mark.django_db
def test_replay_dlq_command_routing_key_format(dead_letter: DeadLetterMessage) -> None:
    """Test that routing key is formatted correctly."""
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        call_command("replay_dlq", "--limit", 10)

        # Check routing key format
        call_args = mock_channel.basic_publish.call_args
        routing_key = call_args[1]["routing_key"]
        assert routing_key == f"{dead_letter.queue_name}.{dead_letter.message_type.lower()}"
