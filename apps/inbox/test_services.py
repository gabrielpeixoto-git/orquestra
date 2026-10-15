"""Tests for inbox services."""

import uuid

import pytest
from django.db import IntegrityError
from django.test import TestCase

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


@pytest.mark.django_db
class TestInboxMessageModel:
    """Test InboxMessage model."""

    def test_inbox_message_str_representation(self):
        """Test string representation of InboxMessage."""
        message_id = uuid.uuid4()
        inbox_msg = InboxMessage.objects.create(
            consumer="test_consumer",
            message_id=message_id,
            message_type="TestMessage",
            payload={"test": "data"},
        )

        str_repr = str(inbox_msg)
        assert "test_consumer" in str_repr
        assert str(message_id) in str_repr

    def test_inbox_message_unique_constraint(self):
        """Test that unique constraint works on consumer + message_id."""
        message_id = uuid.uuid4()
        consumer = "test_consumer"

        # Create first message
        InboxMessage.objects.create(
            consumer=consumer,
            message_id=message_id,
            message_type="TestMessage",
            payload={"test": "data"},
        )

        # Try to create duplicate - should raise IntegrityError
        with pytest.raises(IntegrityError):
            InboxMessage.objects.create(
                consumer=consumer,
                message_id=message_id,
                message_type="TestMessage",
                payload={"test": "data2"},
            )


class InboxURLTests(TestCase):
    """Tests for inbox URLs."""

    def test_inbox_urls_import(self):
        """Test inbox URLs can be imported."""
        from apps.inbox import urls

        assert urls is not None

    def test_process_message_raises_on_non_duplicate_error(self):
        """Test that non-duplicate errors are raised."""
        from unittest.mock import patch

        message_id = uuid.uuid4()
        consumer = "test_consumer"
        message_type = "TestMessage"
        payload = {"test": "data"}

        with (
            patch(
                "apps.inbox.services.InboxMessage.objects.create", side_effect=Exception("DB error")
            ),
            pytest.raises(Exception, match="DB error"),
        ):
            process_message(consumer, message_id, message_type, payload)
