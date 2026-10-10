"""Tests for dashboard views."""

import uuid

import pytest
from django.test import Client

from apps.inventory.models import Product
from apps.orders.models import Order
from apps.outbox.models import DeadLetterMessage


@pytest.mark.django_db
class TestDashboardViews:
    """Test dashboard views."""

    def setup_method(self):
        """Setup test client."""
        self.client = Client()

    def test_overview_view(self):
        """Test overview page renders."""
        response = self.client.get("/")
        assert response.status_code == 200

    def test_orders_view(self):
        """Test orders list page renders."""
        response = self.client.get("/orders/")
        assert response.status_code == 200

    def test_orders_view_with_status_filter(self):
        """Test orders with status filter."""
        response = self.client.get("/orders/?status=PENDING")
        assert response.status_code == 200

    def test_orders_view_with_search(self):
        """Test orders with search."""
        response = self.client.get("/orders/?search=test")
        assert response.status_code == 200

    def test_orders_view_htmx_request(self):
        """Test orders HTMX request returns table body only."""
        response = self.client.get("/orders/", HTTP_HX_Request="true")
        assert response.status_code == 200

    def test_order_detail_view(self):
        """Test order detail page."""
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            total_amount=100.00,
            status=Order.Status.PENDING,
        )
        response = self.client.get(f"/orders/{order.id}/")
        assert response.status_code == 200

    def test_order_detail_view_not_found(self):
        """Test order detail with non-existent order."""
        fake_id = uuid.uuid4()
        response = self.client.get(f"/orders/{fake_id}/")
        assert response.status_code == 404

    def test_dead_letters_view(self):
        """Test dead letters page."""
        response = self.client.get("/dead-letters/")
        assert response.status_code == 200

    def test_dead_letters_view_htmx_request(self):
        """Test dead letters HTMX request."""
        response = self.client.get("/dead-letters/", HTTP_HX_Request="true")
        assert response.status_code == 200

    def test_laboratory_view(self):
        """Test laboratory page."""
        response = self.client.get("/laboratory/")
        assert response.status_code == 200

    def test_health_view(self):
        """Test health page."""
        response = self.client.get("/health/")
        assert response.status_code == 200

    def test_health_view_htmx_request(self):
        """Test health HTMX request."""
        response = self.client.get("/health/", HTTP_HX_Request="true")
        assert response.status_code == 200

    def test_generate_order_post(self):
        """Test generate order POST request."""
        Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test",
            price=100.00,
            stock_quantity=10,
        )
        response = self.client.post("/laboratory/generate-order/")
        assert response.status_code == 200
        assert b"success" in response.content

    def test_generate_order_post_creates_product_if_none(self):
        """Test generate order creates product if none exists."""
        Product.objects.all().delete()
        response = self.client.post("/laboratory/generate-order/")
        assert response.status_code == 200
        assert Product.objects.count() == 1

    def test_generate_order_get_method_not_allowed(self):
        """Test generate order rejects GET."""
        response = self.client.get("/laboratory/generate-order/")
        assert response.status_code == 405

    def test_replay_dead_letter_post(self):
        """Test replay dead letter POST."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="test",
            message_type="TestMessage",
            payload={},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )
        response = self.client.post(f"/dead-letters/{dead_letter.id}/replay/")
        assert response.status_code == 200
        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.REPLAYED

    def test_replay_dead_letter_not_found(self):
        """Test replay dead letter with non-existent ID."""
        fake_id = uuid.uuid4()
        response = self.client.post(f"/dead-letters/{fake_id}/replay/")
        assert response.status_code == 404

    def test_replay_dead_letter_get_method_not_allowed(self):
        """Test replay dead letter rejects GET."""
        fake_id = uuid.uuid4()
        response = self.client.get(f"/dead-letters/{fake_id}/replay/")
        assert response.status_code == 405

    def test_discard_dead_letter_post(self):
        """Test discard dead letter POST."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="test",
            message_type="TestMessage",
            payload={},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )
        response = self.client.post(f"/dead-letters/{dead_letter.id}/discard/")
        assert response.status_code == 200
        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.DISCARDED

    def test_discard_dead_letter_not_found(self):
        """Test discard dead letter with non-existent ID."""
        fake_id = uuid.uuid4()
        response = self.client.post(f"/dead-letters/{fake_id}/discard/")
        assert response.status_code == 404

    def test_discard_dead_letter_get_method_not_allowed(self):
        """Test discard dead letter rejects GET."""
        fake_id = uuid.uuid4()
        response = self.client.get(f"/dead-letters/{fake_id}/discard/")
        assert response.status_code == 405

    def test_inject_failure_payment_timeout(self):
        """Test inject failure for payment timeout."""
        response = self.client.post(
            "/laboratory/inject-failure/",
            {"failure_type": "payment_timeout"},
        )
        assert response.status_code == 200
        assert b"Payment timeout injected" in response.content

    def test_inject_failure_stock_error(self):
        """Test inject failure for stock error."""
        response = self.client.post(
            "/laboratory/inject-failure/",
            {"failure_type": "stock_error"},
        )
        assert response.status_code == 200
        assert b"Stock error injected" in response.content

    def test_inject_failure_invalid_type(self):
        """Test inject failure with invalid type."""
        response = self.client.post(
            "/laboratory/inject-failure/",
            {"failure_type": "invalid"},
        )
        assert response.status_code == 400

    def test_inject_failure_get_method_not_allowed(self):
        """Test inject failure rejects GET."""
        response = self.client.get("/laboratory/inject-failure/")
        assert response.status_code == 405
