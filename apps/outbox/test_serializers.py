"""Tests for outbox serializers."""

import uuid

from django.test import TestCase

from apps.outbox.models import DeadLetterMessage, OutboxMessage
from apps.outbox.serializers import (
    DeadLetterMessageSerializer,
    OutboxMessageSerializer,
    ReplayDeadLetterSerializer,
)


def test_outbox_message_serializer_valid() -> None:
    """Test OutboxMessageSerializer with valid data."""
    data = {
        "message_type": "OrderCreated",
        "payload": {"test": "data"},
        "aggregate_type": "order",
        "aggregate_id": str(uuid.uuid4()),
    }
    serializer = OutboxMessageSerializer(data=data)
    assert serializer.is_valid()


def test_dead_letter_message_serializer_valid() -> None:
    """Test DeadLetterMessageSerializer with valid data."""
    data = {
        "queue_name": "inventory",
        "message_type": "OrderCreated",
        "payload": {"test": "data"},
        "error_message": "Test error",
    }
    serializer = DeadLetterMessageSerializer(data=data)
    assert serializer.is_valid()


def test_replay_dead_letter_serializer_valid() -> None:
    """Test ReplayDeadLetterSerializer with valid data."""
    data = {
        "dead_letter_id": str(uuid.uuid4()),
    }
    serializer = ReplayDeadLetterSerializer(data=data)
    assert serializer.is_valid()


def test_replay_dead_letter_serializer_missing_id() -> None:
    """Test ReplayDeadLetterSerializer with missing dead_letter_id."""
    data = {}
    serializer = ReplayDeadLetterSerializer(data=data)
    assert not serializer.is_valid()
    assert "dead_letter_id" in serializer.errors


class OutboxMessageSerializerTests(TestCase):
    """Tests for OutboxMessageSerializer with model instances."""

    def test_outbox_message_serializer_fields(self):
        """Test OutboxMessageSerializer includes all expected fields."""
        message = OutboxMessage.objects.create(
            message_type="TestMessage",
            payload={"test": "data"},
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
        )

        serializer = OutboxMessageSerializer(message)
        data = serializer.data

        assert "id" in data
        assert "message_type" in data
        assert "payload" in data
        assert "status" in data


class DeadLetterMessageSerializerTests(TestCase):
    """Tests for DeadLetterMessageSerializer with model instances."""

    def test_dead_letter_message_serializer_fields(self):
        """Test DeadLetterMessageSerializer includes all expected fields."""
        dead_letter = DeadLetterMessage.objects.create(
            queue_name="test",
            message_type="TestMessage",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        serializer = DeadLetterMessageSerializer(dead_letter)
        data = serializer.data

        assert "id" in data
        assert "queue_name" in data
        assert "error_message" in data
        assert "status" in data
