"""Tests for outbox serializers."""

import uuid

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
