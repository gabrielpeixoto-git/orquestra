"""Tests for audit handlers."""

import uuid
from unittest.mock import patch

import pytest

from apps.audit.tasks.handlers import handle_all_messages


@pytest.mark.django_db
def test_handle_all_messages_success() -> None:
    """Test successful handling of a message."""
    message = {
        "correlation_id": str(uuid.uuid4()),
        "order_id": str(uuid.uuid4()),
        "data": {"test": "value"},
    }
    message_type = "OrderCreated"

    with patch("apps.audit.tasks.handlers.log_audit") as mock_log_audit:
        handle_all_messages(message, message_type)

        mock_log_audit.assert_called_once()
        call_args = mock_log_audit.call_args
        assert call_args.kwargs["action"] == "ORDERCREATED"
        assert call_args.kwargs["actor"] == "system"
        assert call_args.kwargs["entity_type"] == "ordercreated"


@pytest.mark.django_db
def test_handle_all_messages_idempotent() -> None:
    """Test that duplicate messages are skipped."""
    correlation_id = uuid.uuid4()
    message = {
        "correlation_id": str(correlation_id),
        "order_id": str(uuid.uuid4()),
    }
    message_type = "OrderCreated"

    # First call
    handle_all_messages(message, message_type)

    # Second call (should be idempotent)
    with patch("apps.audit.tasks.handlers.log_audit") as mock_log_audit:
        handle_all_messages(message, message_type)
        mock_log_audit.assert_not_called()
