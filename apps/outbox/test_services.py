"""Tests for outbox services."""

import uuid

import pytest
from django.test import TestCase

from apps.outbox.models import OutboxMessage
from apps.outbox.services import (
    create_outbox_message,
    get_pending_messages,
    mark_message_failed,
    mark_message_published,
)


@pytest.mark.django_db
class TestOutboxServices:
    """Test outbox pattern services."""

    def test_create_outbox_message(self):
        """Test creating an outbox message."""
        message_type = "OrderCreated"
        payload = {"order_id": str(uuid.uuid4()), "amount": 100.0}
        aggregate_type = "order"
        aggregate_id = uuid.uuid4()
        correlation_id = uuid.uuid4()
        causation_id = uuid.uuid4()

        message = create_outbox_message(
            message_type=message_type,
            payload=payload,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        assert message.message_type == message_type
        assert message.payload == payload
        assert message.aggregate_type == aggregate_type
        assert message.aggregate_id == aggregate_id
        assert message.correlation_id == correlation_id
        assert message.causation_id == causation_id
        assert message.status == OutboxMessage.Status.PENDING

    def test_create_outbox_message_without_causation(self):
        """Test creating an outbox message without causation ID."""
        message_type = "OrderCreated"
        payload = {"order_id": str(uuid.uuid4())}
        aggregate_type = "order"
        aggregate_id = uuid.uuid4()
        correlation_id = uuid.uuid4()

        message = create_outbox_message(
            message_type=message_type,
            payload=payload,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            correlation_id=correlation_id,
        )

        assert message.causation_id is None

    def test_mark_message_published(self):
        """Test marking a message as published."""
        message = OutboxMessage.objects.create(
            message_type="TestMessage",
            payload={},
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            status=OutboxMessage.Status.PENDING,
        )

        updated = mark_message_published(message.id)

        assert updated.status == OutboxMessage.Status.PUBLISHED

    def test_mark_message_failed(self):
        """Test marking a message as failed."""
        message = OutboxMessage.objects.create(
            message_type="TestMessage",
            payload={"original": "data"},
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            status=OutboxMessage.Status.PENDING,
        )
        error_msg = "Connection timeout"

        updated = mark_message_failed(message.id, error_msg)

        assert updated.status == OutboxMessage.Status.FAILED
        assert "_error" in updated.payload
        assert updated.payload["_error"] == error_msg

    def test_get_pending_messages(self):
        """Test retrieving pending messages."""
        # Create pending messages
        for i in range(3):
            OutboxMessage.objects.create(
                message_type=f"TestMessage{i}",
                payload={},
                aggregate_type="test",
                aggregate_id=uuid.uuid4(),
                correlation_id=uuid.uuid4(),
                status=OutboxMessage.Status.PENDING,
            )

        # Create a published message (should not be included)
        OutboxMessage.objects.create(
            message_type="PublishedMessage",
            payload={},
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            status=OutboxMessage.Status.PUBLISHED,
        )

        pending = get_pending_messages(limit=10)

        assert len(pending) == 3
        assert all(msg.status == OutboxMessage.Status.PENDING for msg in pending)

    def test_get_pending_messages_with_limit(self):
        """Test retrieving pending messages with limit."""
        # Create 5 pending messages
        for i in range(5):
            OutboxMessage.objects.create(
                message_type=f"TestMessage{i}",
                payload={},
                aggregate_type="test",
                aggregate_id=uuid.uuid4(),
                correlation_id=uuid.uuid4(),
                status=OutboxMessage.Status.PENDING,
            )

        pending = get_pending_messages(limit=3)

        assert len(pending) == 3

    def test_get_pending_messages_empty(self):
        """Test retrieving pending messages when none exist."""
        pending = get_pending_messages()
        assert pending == []

    def test_mark_message_published_nonexistent(self):
        """Test marking a non-existent message as published."""
        with pytest.raises(OutboxMessage.DoesNotExist):
            mark_message_published(uuid.uuid4())

    def test_mark_message_failed_nonexistent(self):
        """Test marking a non-existent message as failed."""
        with pytest.raises(OutboxMessage.DoesNotExist):
            mark_message_failed(uuid.uuid4(), "test error")


class OutboxMessageModelTests(TestCase):
    """Tests for OutboxMessage model."""

    def test_outbox_message_str_representation(self) -> None:
        """Test string representation of OutboxMessage."""
        message = OutboxMessage.objects.create(
            message_type="OrderCreated",
            payload={"test": "data"},
            aggregate_type="order",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            status=OutboxMessage.Status.PENDING,
        )

        str_repr = str(message)
        assert "OutboxMessage" in str_repr
        assert str(message.id) in str_repr
        assert "OrderCreated" in str_repr
        assert "PENDING" in str_repr


class DeadLetterMessageModelTests(TestCase):
    """Tests for DeadLetterMessage model."""

    def test_dead_letter_message_str_representation(self) -> None:
        """Test string representation of DeadLetterMessage."""
        from apps.outbox.models import DeadLetterMessage

        dead_letter = DeadLetterMessage.objects.create(
            queue_name="payments",
            message_type="PaymentProcessed",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        str_repr = str(dead_letter)
        assert "DeadLetterMessage" in str_repr
        assert str(dead_letter.id) in str_repr
        assert "payments" in str_repr
        assert "PENDING" in str_repr
