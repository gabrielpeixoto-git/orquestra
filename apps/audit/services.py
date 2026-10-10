"""Services for audit logging."""

import uuid

import structlog

from apps.audit.models import AuditLog

logger = structlog.get_logger(__name__)


def log_audit(
    action: str,
    actor: str,
    entity_type: str,
    entity_id: uuid.UUID,
    changes: dict | None = None,
) -> AuditLog:
    """Log an audit event.

    Args:
        action: Action performed (e.g., "ORDER_CREATED", "PAYMENT_PROCESSED").
        actor: String identifier of the actor who performed the action.
        entity_type: Type of resource affected (e.g., "order", "payment").
        entity_id: UUID of the resource affected.
        changes: Optional changes dictionary.

    Returns:
        The created AuditLog instance.
    """
    logger.info(
        "Logging audit event",
        action=action,
        actor=actor,
        entity_type=entity_type,
        entity_id=str(entity_id),
    )

    audit_log = AuditLog.objects.create(
        id=uuid.uuid4(),
        action=action,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes or {},
    )

    logger.info(
        "Audit log created successfully",
        audit_log_id=str(audit_log.id),
        action=action,
    )
    return audit_log


def get_audit_log(audit_log_id: uuid.UUID) -> AuditLog:
    """Get an audit log by ID.

    Args:
        audit_log_id: UUID of the audit log.

    Returns:
        The AuditLog instance.

    Raises:
        AuditLog.DoesNotExist: If audit log does not exist.
    """
    try:
        return AuditLog.objects.get(id=audit_log_id)
    except AuditLog.DoesNotExist:
        logger.exception("Audit log not found", audit_log_id=str(audit_log_id))
        raise
