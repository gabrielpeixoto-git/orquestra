"""Tests for outbox API views."""

import uuid

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.outbox.models import DeadLetterMessage, OutboxMessage


@pytest.mark.django_db
@pytest.mark.integration
class ListOutboxMessagesTests:
    """Tests for GET /api/v1/outbox/ endpoint."""

    def test_list_outbox_messages_success(self) -> None:
        """Test listing outbox messages as staff."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

        OutboxMessage.objects.create(
            id=uuid.uuid4(),
            message_type="OrderCreated",
            payload={"test": "data"},
            aggregate_type="order",
            aggregate_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            status=OutboxMessage.Status.PENDING,
        )

        response = client.get("/staff/outbox/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["message_type"] == "OrderCreated"

    def test_list_outbox_messages_unauthorized(self) -> None:
        """Test listing outbox messages without staff permission."""
        client = APIClient()
        client.force_authenticate(user=None)
        response = client.get("/staff/outbox/")

        assert response.status_code in (401, 403)


@pytest.mark.django_db
@pytest.mark.integration
class ListDeadLettersTests:
    """Tests for GET /api/v1/dead-letters/ endpoint."""

    def test_list_dead_letters_success(self) -> None:
        """Test listing dead letter messages as staff."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

        DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        response = client.get("/staff/dead-letters/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["queue_name"] == "inventory"

    def test_list_dead_letters_filtered_by_queue(self) -> None:
        """Test listing dead letters filtered by queue."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

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

        response = client.get("/staff/dead-letters/?queue=inventory")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["queue_name"] == "inventory"

    def test_list_dead_letters_unauthorized(self) -> None:
        """Test listing dead letters without staff permission."""
        client = APIClient()
        client.force_authenticate(user=None)
        response = client.get("/staff/dead-letters/")

        assert response.status_code in (401, 403)


@pytest.mark.django_db
@pytest.mark.integration
class ReplayDeadLetterTests:
    """Tests for POST /api/v1/dead-letters/replay/ endpoint."""

    def test_replay_dead_letter_success(self) -> None:
        """Test replaying a dead letter message as staff."""
        from unittest.mock import patch

        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

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
            response = client.post(
                "/staff/dead-letters/replay/",
                {"dead_letter_id": str(dead_letter.id)},
                format="json",
            )

        assert response.status_code == 200
        assert response.data["message"] == "Message replayed successfully"

    def test_replay_dead_letter_not_found(self) -> None:
        """Test replaying a non-existent dead letter."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

        response = client.post(
            "/staff/dead-letters/replay/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code == 404
        assert "not found" in response.data["error"]

    def test_replay_dead_letter_invalid_status(self) -> None:
        """Test replaying a dead letter that is not pending."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.DISCARDED,
        )

        response = client.post(
            "/staff/dead-letters/replay/",
            {"dead_letter_id": str(dead_letter.id)},
            format="json",
        )

        assert response.status_code == 400
        assert "not in pending status" in response.data["error"]

    def test_replay_dead_letter_unauthorized(self) -> None:
        """Test replaying a dead letter without staff permission."""
        client = APIClient()
        client.force_authenticate(user=None)
        response = client.post(
            "/staff/dead-letters/replay/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code in (401, 403)


@pytest.mark.django_db
@pytest.mark.integration
class DiscardDeadLetterTests:
    """Tests for POST /api/v1/dead-letters/discard/ endpoint."""

    def test_discard_dead_letter_success(self) -> None:
        """Test discarding a dead letter message as staff."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        response = client.post(
            "/staff/dead-letters/discard/",
            {"dead_letter_id": str(dead_letter.id)},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["message"] == "Message discarded successfully"

        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.DISCARDED

    def test_discard_dead_letter_not_found(self) -> None:
        """Test discarding a non-existent dead letter."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

        response = client.post(
            "/staff/dead-letters/discard/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code == 404
        assert "not found" in response.data["error"]

    def test_discard_dead_letter_invalid_status(self) -> None:
        """Test discarding a dead letter that is not pending."""
        client = APIClient()
        staff_user = User.objects.create_user(username="staff", is_staff=True, is_superuser=True)
        client.force_authenticate(user=staff_user)

        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="inventory",
            message_type="OrderCreated",
            payload={"test": "data"},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.DISCARDED,
        )

        response = client.post(
            "/staff/dead-letters/discard/",
            {"dead_letter_id": str(dead_letter.id)},
            format="json",
        )

        assert response.status_code == 400
        assert "not in pending status" in response.data["error"]

    def test_discard_dead_letter_unauthorized(self) -> None:
        """Test discarding a dead letter without staff permission."""
        client = APIClient()
        client.force_authenticate(user=None)
        response = client.post(
            "/staff/dead-letters/discard/",
            {"dead_letter_id": str(uuid.uuid4())},
            format="json",
        )

        assert response.status_code in (401, 403)
