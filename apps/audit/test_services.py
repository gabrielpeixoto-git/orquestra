"""Tests for audit services."""

import uuid

import pytest
from django.test import TestCase

from apps.audit.models import AuditLog
from apps.audit.services import get_audit_log, log_audit


class LogAuditTests(TestCase):
    """Tests for log_audit service."""

    def test_log_audit(self) -> None:
        """Test logging an audit event."""
        actor = "user@example.com"
        entity_id = uuid.uuid4()
        action = "ORDER_CREATED"
        entity_type = "order"

        audit_log = log_audit(
            action=action,
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        assert audit_log.action == action
        assert audit_log.actor == actor
        assert audit_log.entity_type == entity_type
        assert audit_log.entity_id == entity_id

    def test_log_audit_with_details(self) -> None:
        """Test logging an audit event with details."""
        actor = "user@example.com"
        entity_id = uuid.uuid4()
        changes = {"amount": "100.00", "status": "succeeded"}

        audit_log = log_audit(
            action="PAYMENT_PROCESSED",
            actor=actor,
            entity_type="payment",
            entity_id=entity_id,
            changes=changes,
        )

        assert audit_log.changes == changes

    def test_log_audit_without_actor(self) -> None:
        """Test logging an audit event without an actor."""
        entity_id = uuid.uuid4()

        audit_log = log_audit(
            action="SYSTEM_EVENT",
            actor="system",
            entity_type="system",
            entity_id=entity_id,
        )

        assert audit_log.actor == "system"


class GetAuditLogTests(TestCase):
    """Tests for get_audit_log service."""

    def test_get_existing_audit_log(self) -> None:
        """Test getting an existing audit log."""
        audit_log_id = uuid.uuid4()
        AuditLog.objects.create(
            id=audit_log_id,
            action="ORDER_CREATED",
            actor="user@example.com",
            entity_type="order",
            entity_id=uuid.uuid4(),
        )

        audit_log = get_audit_log(audit_log_id)

        assert audit_log.id == audit_log_id

    def test_get_nonexistent_audit_log_raises_error(self) -> None:
        """Test getting a non-existent audit log raises error."""
        audit_log_id = uuid.uuid4()

        with pytest.raises(AuditLog.DoesNotExist):
            get_audit_log(audit_log_id)


class AuditLogModelTests(TestCase):
    """Tests for AuditLog model."""

    def test_audit_log_str_representation(self) -> None:
        """Test string representation of AuditLog."""
        audit_log = AuditLog.objects.create(
            id=uuid.uuid4(),
            action="ORDER_CREATED",
            actor="user@example.com",
            entity_type="order",
            entity_id=uuid.uuid4(),
        )

        str_repr = str(audit_log)
        assert "ORDER_CREATED" in str_repr

    def test_audit_log_choices(self) -> None:
        """Test AuditLog choices work correctly."""
        audit_log = AuditLog.objects.create(
            id=uuid.uuid4(),
            action="ORDER_CREATED",
            actor="user@example.com",
            entity_type="order",
            entity_id=uuid.uuid4(),
        )

        assert audit_log.action == "ORDER_CREATED"
        assert audit_log.entity_type == "order"

    def test_audit_log_with_json_changes(self):
        """Test AuditLog with JSON changes field."""
        audit_log = AuditLog.objects.create(
            id=uuid.uuid4(),
            action=AuditLog.Action.ORDER_CREATED,
            actor="user@example.com",
            entity_type="order",
            entity_id=uuid.uuid4(),
            changes={"key": "value", "nested": {"data": "test"}},
        )

        assert audit_log.changes == {"key": "value", "nested": {"data": "test"}}


class AuditURLTests(TestCase):
    """Tests for audit URLs."""

    def test_audit_urls_import(self):
        """Test audit URLs can be imported."""
        from apps.audit import urls

        assert urls is not None
