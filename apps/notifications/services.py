"""Services for notification management."""

import uuid

import structlog

from apps.notifications.models import Notification

logger = structlog.get_logger(__name__)


class NotificationError(Exception):
    """Error raised when notification fails."""


def send_notification(
    recipient: str,
    notification_type: str,
    subject: str,
    body: str,
    metadata: dict | None = None,
) -> Notification:
    """Send a notification to a recipient.

    Args:
        recipient: String identifier of the recipient (email or phone).
        notification_type: Type of notification (e.g., "EMAIL", "SMS").
        subject: Notification subject/title.
        body: Notification body.
        metadata: Optional metadata dictionary.

    Returns:
        The created Notification instance.
    """
    logger.info(
        "Sending notification",
        recipient=recipient,
        notification_type=notification_type,
        subject=subject,
    )

    notification = Notification.objects.create(
        id=uuid.uuid4(),
        recipient=recipient,
        type=notification_type,
        subject=subject,
        body=body,
        metadata=metadata or {},
    )

    logger.info(
        "Notification sent successfully",
        notification_id=str(notification.id),
        recipient=recipient,
    )
    return notification


def get_notification(notification_id: uuid.UUID) -> Notification:
    """Get a notification by ID.

    Args:
        notification_id: UUID of the notification.

    Returns:
        The Notification instance.

    Raises:
        Notification.DoesNotExist: If notification does not exist.
    """
    try:
        return Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error("Notification not found", notification_id=str(notification_id))
        raise
