"""Tests for notification services."""

import uuid

import pytest
from django.test import TestCase

from apps.notifications.models import Notification
from apps.notifications.services import get_notification, send_notification


class SendNotificationTests(TestCase):
    """Tests for send_notification service."""

    def test_send_notification(self) -> None:
        """Test sending a notification."""
        recipient = "user@example.com"
        notification_type = "EMAIL"
        subject = "Order Created"
        body = "Your order has been created successfully."

        notification = send_notification(
            recipient=recipient,
            notification_type=notification_type,
            subject=subject,
            body=body,
        )

        assert notification.recipient == recipient
        assert notification.type == notification_type
        assert notification.subject == subject
        assert notification.body == body

    def test_send_notification_with_metadata(self) -> None:
        """Test sending a notification with metadata."""
        recipient = "user@example.com"
        metadata = {"order_id": str(uuid.uuid4()), "amount": "100.00"}

        notification = send_notification(
            recipient=recipient,
            notification_type="EMAIL",
            subject="Payment Failed",
            body="Your payment could not be processed.",
            metadata=metadata,
        )

        assert notification.metadata == metadata

    def test_send_notification_sms_type(self) -> None:
        """Test sending an SMS notification."""
        notification = send_notification(
            recipient="+5511999999999",
            notification_type="SMS",
            subject="SMS Alert",
            body="Your order has been shipped",
        )

        assert notification.type == "SMS"
        assert notification.recipient == "+5511999999999"


class GetNotificationTests(TestCase):
    """Tests for get_notification service."""

    def test_get_existing_notification(self) -> None:
        """Test getting an existing notification."""
        notification_id = uuid.uuid4()
        Notification.objects.create(
            id=notification_id,
            recipient="user@example.com",
            type="EMAIL",
            subject="Order Created",
            body="Your order has been created successfully.",
        )

        notification = get_notification(notification_id)

        assert notification.id == notification_id

    def test_get_nonexistent_notification_raises_error(self) -> None:
        """Test getting a non-existent notification raises error."""
        notification_id = uuid.uuid4()

        with pytest.raises(Notification.DoesNotExist):
            get_notification(notification_id)


class NotificationModelTests(TestCase):
    """Tests for Notification model."""

    def test_notification_str_representation(self) -> None:
        """Test string representation of Notification."""
        notification = Notification.objects.create(
            id=uuid.uuid4(),
            recipient="user@example.com",
            type=Notification.Type.EMAIL,
            status=Notification.Status.SENT,
            subject="Test Subject",
            body="Test body",
        )

        str_repr = str(notification)
        assert "Notification" in str_repr
        assert str(notification.id) in str_repr
        assert "EMAIL" in str_repr
        assert "user@example.com" in str_repr


class NotificationsURLTests(TestCase):
    """Tests for notifications URLs."""

    def test_notifications_urls_import(self):
        """Test notifications URLs can be imported."""
        from apps.notifications import urls

        assert urls is not None
