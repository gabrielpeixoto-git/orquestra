"""Tests for dead letter services."""

import uuid

import pytest
from celery.exceptions import MaxRetriesExceededError
from django.test import TestCase
from kombu.exceptions import OperationalError

from apps.outbox.models import DeadLetterMessage
from apps.outbox.services_deadletter import (
    create_dead_letter,
    get_pending_dead_letters,
    handle_dead_letter,
    mark_dead_letter_discarded,
    mark_dead_letter_replayed,
    should_send_to_dlq,
)


class CreateDeadLetterTests(TestCase):
    """Tests for create_dead_letter service."""

    def test_create_dead_letter_success(self) -> None:
        """Test creating a dead letter message."""
        queue_name = "test_queue"
        message_type = "TestMessage"
        payload = {"key": "value"}
        error_message = "Test error"
        correlation_id = uuid.uuid4()
        retry_count = 3

        dead_letter = create_dead_letter(
            queue_name=queue_name,
            message_type=message_type,
            payload=payload,
            error_message=error_message,
            correlation_id=correlation_id,
            retry_count=retry_count,
        )

        assert dead_letter.queue_name == queue_name
        assert dead_letter.message_type == message_type
        assert dead_letter.payload == payload
        assert dead_letter.error_message == error_message
        assert dead_letter.correlation_id == correlation_id
        assert dead_letter.retry_count == retry_count
        assert dead_letter.status == DeadLetterMessage.Status.PENDING


class GetPendingDeadLettersTests(TestCase):
    """Tests for get_pending_dead_letters service."""

    def test_get_pending_dead_letters_all(self) -> None:
        """Test getting all pending dead letters."""
        # Create pending dead letters
        for i in range(3):
            DeadLetterMessage.objects.create(
                id=uuid.uuid4(),
                queue_name="test_queue",
                message_type="TestMessage",
                payload={"key": f"value_{i}"},
                error_message="Test error",
                correlation_id=uuid.uuid4(),
                retry_count=0,
            )

        # Create a non-pending dead letter
        DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="test_queue",
            message_type="TestMessage",
            payload={"key": "value"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            retry_count=0,
            status=DeadLetterMessage.Status.REPLAYED,
        )

        pending = get_pending_dead_letters()
        assert len(pending) == 3

    def test_get_pending_dead_letters_with_queue_filter(self) -> None:
        """Test getting pending dead letters filtered by queue."""
        # Create dead letters for different queues
        DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="queue_a",
            message_type="TestMessage",
            payload={"key": "value"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            retry_count=0,
        )
        DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="queue_b",
            message_type="TestMessage",
            payload={"key": "value"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            retry_count=0,
        )

        pending = get_pending_dead_letters(queue_name="queue_a")
        assert len(pending) == 1
        assert pending[0].queue_name == "queue_a"

    def test_get_pending_dead_letters_with_limit(self) -> None:
        """Test getting pending dead letters with limit."""
        # Create 5 pending dead letters
        for i in range(5):
            DeadLetterMessage.objects.create(
                id=uuid.uuid4(),
                queue_name="test_queue",
                message_type="TestMessage",
                payload={"key": f"value_{i}"},
                error_message="Test error",
                correlation_id=uuid.uuid4(),
                retry_count=0,
            )

        pending = get_pending_dead_letters(limit=3)
        assert len(pending) == 3


class MarkDeadLetterReplayedTests(TestCase):
    """Tests for mark_dead_letter_replayed service."""

    def test_mark_dead_letter_replayed(self) -> None:
        """Test marking a dead letter as replayed."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="test_queue",
            message_type="TestMessage",
            payload={"key": "value"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            retry_count=0,
        )

        mark_dead_letter_replayed(dead_letter.id)

        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.REPLAYED


class MarkDeadLetterDiscardedTests(TestCase):
    """Tests for mark_dead_letter_discarded service."""

    def test_mark_dead_letter_discarded(self) -> None:
        """Test marking a dead letter as discarded."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="test_queue",
            message_type="TestMessage",
            payload={"key": "value"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            retry_count=0,
        )

        mark_dead_letter_discarded(dead_letter.id)

        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.DISCARDED


class ShouldSendToDlqTests(TestCase):
    """Tests for should_send_to_dlq service."""

    def test_should_send_to_dlq_max_retries_exceeded(self) -> None:
        """Test that MaxRetriesExceededError should send to DLQ."""
        exception = MaxRetriesExceededError("Max retries exceeded")
        assert should_send_to_dlq(exception) is True

    def test_should_send_to_dlq_operational_error(self) -> None:
        """Test that OperationalError should send to DLQ."""
        exception = OperationalError("Connection error")
        assert should_send_to_dlq(exception) is True

    def test_should_send_to_dlq_other_exception(self) -> None:
        """Test that other exceptions should not send to DLQ."""
        exception = ValueError("Invalid value")
        assert should_send_to_dlq(exception) is False


class HandleDeadLetterTests(TestCase):
    """Tests for handle_dead_letter service."""

    def test_handle_dead_letter(self) -> None:
        """Test handling a dead letter."""
        queue_name = "test_queue"
        message_type = "TestMessage"
        payload = {"key": "value"}
        error_message = "Test error"
        correlation_id = uuid.uuid4()
        retry_count = 3

        dead_letter = handle_dead_letter(
            queue_name=queue_name,
            message_type=message_type,
            payload=payload,
            error_message=error_message,
            correlation_id=correlation_id,
            retry_count=retry_count,
        )

        assert dead_letter.queue_name == queue_name
        assert dead_letter.message_type == message_type
        assert dead_letter.payload == payload
        assert dead_letter.error_message == error_message
        assert dead_letter.correlation_id == correlation_id
        assert dead_letter.retry_count == retry_count
