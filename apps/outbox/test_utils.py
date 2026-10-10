"""Tests for outbox utils."""

import uuid

import pytest

from apps.outbox.utils import handle_dead_letter


@pytest.mark.django_db
class TestOutboxUtils:
    """Test outbox utility functions."""

    def test_handle_dead_letter(self):
        """Test handling a dead letter message."""
        from apps.outbox.models import DeadLetterMessage

        queue_name = "test_queue"
        message_type = "TestMessage"
        message = {"test": "data"}
        correlation_id = uuid.uuid4()
        exception = Exception("Test error")

        handle_dead_letter(
            queue_name=queue_name,
            message_type=message_type,
            message=message,
            correlation_id=correlation_id,
            exception=exception,
            retry_count=3,
        )

        # Verify dead letter was created
        dead_letter = DeadLetterMessage.objects.get(correlation_id=correlation_id)
        assert dead_letter.queue_name == queue_name
        assert dead_letter.message_type == message_type
        assert dead_letter.payload == message
        assert "Test error" in dead_letter.error_message
        assert dead_letter.retry_count == 3
