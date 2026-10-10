"""Tests for inbox services."""

import uuid

import pytest

from apps.inbox.models import InboxMessage
from apps.inbox.services import DuplicateMessageError, is_message_processed, process_message


@pytest.mark.django_db
class TestInboxServices:
    """Test inbox pattern services."""

    def test_process_message_success(self):
        """Test successful message processing."""
        message_id = uuid.uuid4()
        consumer = "test_consumer"
        message_type = "TestMessage"
        payload = {"test": "data"}

        inbox_msg = process_message(consumer, message_id, message_type, payload)

        assert inbox_msg.consumer == consumer
        assert inbox_msg.message_id == message_id
        assert inbox_msg.message_type == message_type
        assert inbox_msg.payload == payload

    def test_process_message_duplicate(self):
        """Test duplicate message raises DuplicateMessageError."""
        message_id = uuid.uuid4()
        consumer = "test_consumer"
        message_type = "TestMessage"
        payload = {"test": "data"}

        # Process first time
        process_message(consumer, message_id, message_type, payload)

        # Try to process again
        with pytest.raises(DuplicateMessageError):
            process_message(consumer, message_id, message_type, payload)

    def test_is_message_processed_true(self):
        """Test is_message_processed returns True when processed."""
        message_id = uuid.uuid4()
        consumer = "test_consumer"

        # Create inbox message
        InboxMessage.objects.create(
            consumer=consumer,
            message_id=message_id,
            message_type="TestMessage",
            payload={},
        )

        assert is_message_processed(consumer, message_id) is True

    def test_is_message_processed_false(self):
        """Test is_message_processed returns False when not processed."""
        message_id = uuid.uuid4()
        consumer = "test_consumer"

        assert is_message_processed(consumer, message_id) is False

    def test_is_message_processed_different_consumer(self):
        """Test is_message_processed returns False for different consumer."""
        message_id = uuid.uuid4()
        consumer1 = "consumer1"
        consumer2 = "consumer2"

        # Process with consumer1
        InboxMessage.objects.create(
            consumer=consumer1,
            message_id=message_id,
            message_type="TestMessage",
            payload={},
        )

        # Check with consumer2
        assert is_message_processed(consumer2, message_id) is False
