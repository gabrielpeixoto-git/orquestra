"""Tests for outbox API views."""

import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.outbox.models import DeadLetterMessage, OutboxMessage


class ListOutboxMessagesTests(TestCase):
    """Tests for GET /api/v1/outbox/ endpoint."""

    def setUp(self) -> None:
        """Set up test client and staff user."""
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="staff", is_staff=True, is_superuser=True
        )
        self.client.force_authenticate(user=self.staff_user)

    def test_list_outbox_messages_success(self) -> None:
        """Test listing outbox messages as staff."""
        OutboxMessage.objects.create(
            id=uuid.uuid4(),
            message_type="OrderCreated",
            payload={"test": "data"},
            aggregate_type="order",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            status=OutboxMessage.Status.PENDING,
        )

        response = self.client.get("/api/v1/staff/outbox/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["message_type"] == "OrderCreated"

    def test_list_outbox_messages_unauthorized(self) -> None:
        """Test listing outbox messages without staff permission."""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/staff/outbox/")

        assert response.status_code in (401, 403)


class ListDeadLettersTests(TestCase):
    """Tests for GET /api/v1/dead-letters/ endpoint."""

    def setUp(self) -> None:
        """Set up test client and staff user."""
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="staff", is_staff=True, is_superuser=True
        )
        self.client.force_authenticate(user=self.staff_user)

    def test_list_dead_letters_success(self) -> None:
        """Test listing dead letter messages as staff."""
        DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        response = self.client.get("/api/v1/staff/dead-letters/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["queue_name"] == "inventory"

    def test_list_dead_letters_filtered_by_queue(self) -> None:
        """Test listing dead letters filtered by queue."""
        DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )
        DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="payments",
            message_type="PaymentProcessed",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        response = self.client.get("/api/v1/staff/dead-letters/?queue=inventory")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["queue_name"] == "inventory"

    def test_list_dead_letters_unauthorized(self) -> None:
        """Test listing dead letters without staff permission."""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/staff/dead-letters/")

        assert response.status_code in (401, 403)


class ReplayDeadLetterTests(TestCase):
    """Tests for POST /api/v1/dead-letters/replay/ endpoint."""

    def setUp(self) -> None:
        """Set up test client and staff user."""
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="staff", is_staff=True, is_superuser=True
        )
        self.client.force_authenticate(user=self.staff_user)

    def test_replay_dead_letter_success(self) -> None:
        """Test replaying a dead letter message as staff."""
        from unittest.mock import patch

        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        with patch("apps.outbox.views.call_command"):
            response = self.client.post(
                "/api/v1/staff/dead-letters/replay/",
                {"dead_letter_id": str(dead_letter.id)},
                format="json",
            )

        assert response.status_code == 200
        assert response.data["message"] == "Message replayed successfully"

    def test_replay_dead_letter_not_found(self) -> None:
        """Test replaying a non-existent dead letter."""
        response = self.client.post(
            "/api/v1/staff/dead-letters/replay/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code == 404
        assert "not found" in response.data["error"]

    def test_replay_dead_letter_invalid_status(self) -> None:
        """Test replaying a dead letter that is not pending."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.DISCARDED,
        )

        response = self.client.post(
            "/api/v1/staff/dead-letters/replay/",
            {"dead_letter_id": str(dead_letter.id)},
            format="json",
        )

        assert response.status_code == 400
        assert "not in pending status" in response.data["error"]

    def test_replay_dead_letter_unauthorized(self) -> None:
        """Test replaying a dead letter without staff permission."""
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/v1/staff/dead-letters/replay/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code in (401, 403)


class DiscardDeadLetterTests(TestCase):
    """Tests for POST /api/v1/dead-letters/discard/ endpoint."""

    def setUp(self) -> None:
        """Set up test client and staff user."""
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="staff", is_staff=True, is_superuser=True
        )
        self.client.force_authenticate(user=self.staff_user)

    def test_discard_dead_letter_success(self) -> None:
        """Test discarding a dead letter message as staff."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        response = self.client.post(
            "/api/v1/staff/dead-letters/discard/",
            {"dead_letter_id": str(dead_letter.id)},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["message"] == "Message discarded successfully"

        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.DISCARDED

    def test_discard_dead_letter_not_found(self) -> None:
        """Test discarding a non-existent dead letter."""
        response = self.client.post(
            "/api/v1/staff/dead-letters/discard/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code == 404
        assert "not found" in response.data["error"]

    def test_discard_dead_letter_invalid_status(self) -> None:
        """Test discarding a dead letter that is not pending."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.DISCARDED,
        )

        response = self.client.post(
            "/api/v1/staff/dead-letters/discard/",
            {"dead_letter_id": str(dead_letter.id)},
            format="json",
        )

        assert response.status_code == 400
        assert "not in pending status" in response.data["error"]

    def test_discard_dead_letter_unauthorized(self) -> None:
        """Test discarding a dead letter without staff permission."""
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/v1/staff/dead-letters/discard/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code in (401, 403)
