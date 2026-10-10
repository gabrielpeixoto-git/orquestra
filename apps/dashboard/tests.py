"""Tests for dashboard views."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.inventory.models import Product
from apps.orders.models import Order, OrderItem
from apps.outbox.models import DeadLetterMessage, OutboxMessage

User = get_user_model()


@pytest.mark.django_db
class TestDashboardViews:
    """Test dashboard views."""

    def test_overview_view(self, client):
        """Test overview view renders correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert "total_orders" in response.context

    def test_orders_view(self, client):
        """Test orders view renders correctly."""
        response = client.get("/orders/")
        assert response.status_code == 200
        assert "orders" in response.context

    def test_orders_view_with_filters(self, client):
        """Test orders view with status filter."""
        response = client.get("/orders/?status=PENDING")
        assert response.status_code == 200

    def test_orders_view_with_search(self, client):
        """Test orders view with search."""
        response = client.get("/orders/?search=test")
        assert response.status_code == 200

    def test_orders_view_htmx_request(self, client):
        """Test orders view returns table body for HTMX requests."""
        response = client.get("/orders/", HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        # Should return only the table body
        assert any("orders_table_body.html" in t.name for t in response.templates)

    def test_order_detail_view(self, client):
        """Test order detail view."""
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            total_amount=100.00,
            status=Order.Status.PENDING,
        )
        response = client.get(f"/orders/{order.id}/")
        assert response.status_code == 200
        assert response.context["order"] == order

    def test_order_detail_view_not_found(self, client):
        """Test order detail view with non-existent order."""
        response = client.get(f"/orders/{uuid.uuid4()}/")
        assert response.status_code == 404

    def test_dead_letters_view(self, client):
        """Test dead letters view."""
        response = client.get("/dead-letters/")
        assert response.status_code == 200
        assert "dead_letters" in response.context

    def test_dead_letters_view_htmx_request(self, client):
        """Test dead letters view returns table body for HTMX requests."""
        response = client.get("/dead-letters/", HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert any("dead_letters_table_body.html" in t.name for t in response.templates)

    def test_laboratory_view(self, client):
        """Test laboratory view."""
        response = client.get("/laboratory/")
        assert response.status_code == 200

    def test_health_view(self, client):
        """Test health view."""
        response = client.get("/health/")
        assert response.status_code == 200

    def test_health_view_htmx_request(self, client):
        """Test health view returns content for HTMX requests."""
        response = client.get("/health/", HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert any("health_content.html" in t.name for t in response.templates)


@pytest.mark.django_db
class TestGenerateOrder:
    """Test generate order functionality."""

    def test_generate_order_success(self, client):
        """Test generating a test order successfully."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test",
            price=100.00,
            stock_quantity=100,
        )

        response = client.post("/laboratory/generate-order/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "order_id" in data

        # Verify order was created
        order = Order.objects.get(id=data["order_id"])
        assert order.status == Order.Status.PENDING
        assert order.total_amount == product.price

    def test_generate_order_creates_product_if_none_exists(self, client):
        """Test generating order creates a product if none exists."""
        response = client.post("/laboratory/generate-order/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify product was created
        assert Product.objects.filter(name="Test Product").exists()

    def test_generate_order_method_not_allowed(self, client):
        """Test generate order rejects GET requests."""
        response = client.get("/laboratory/generate-order/")
        assert response.status_code == 405


@pytest.mark.django_db
class TestInjectFailure:
    """Test inject failure functionality."""

    def test_inject_payment_timeout(self, client):
        """Test injecting payment timeout failure."""
        response = client.post(
            "/laboratory/inject-failure/", data={"failure_type": "payment_timeout"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dead_letter_id" in data

        # Verify dead letter was created
        dead_letter = DeadLetterMessage.objects.get(id=data["dead_letter_id"])
        assert dead_letter.queue_name == "payments"
        assert dead_letter.message_type == "PaymentFailed"
        assert "timeout" in dead_letter.error_message.lower()

    def test_inject_stock_error(self, client):
        """Test injecting stock error failure."""
        response = client.post("/laboratory/inject-failure/", data={"failure_type": "stock_error"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify dead letter was created
        dead_letter = DeadLetterMessage.objects.get(id=data["dead_letter_id"])
        assert dead_letter.queue_name == "inventory"
        assert dead_letter.message_type == "StockReservationFailed"

    def test_inject_failure_invalid_type(self, client):
        """Test injecting failure with invalid type."""
        response = client.post("/laboratory/inject-failure/", data={"failure_type": "invalid"})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_inject_failure_method_not_allowed(self, client):
        """Test inject failure rejects GET requests."""
        response = client.get("/laboratory/inject-failure/")
        assert response.status_code == 405


@pytest.mark.django_db
class TestDeadLetterActions:
    """Test dead letter replay and discard actions."""

    def test_replay_dead_letter_success(self, client):
        """Test replaying a dead letter successfully."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="payments",
            message_type="PaymentFailed",
            payload={"order_id": str(uuid.uuid4())},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        response = client.post(f"/dead-letters/{dead_letter.id}/replay/", data={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify status was updated
        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.REPLAYED

    def test_replay_dead_letter_not_found(self, client):
        """Test replaying non-existent dead letter."""
        response = client.post(f"/dead-letters/{uuid.uuid4()}/replay/", data={})
        assert response.status_code == 404

    def test_replay_dead_letter_method_not_allowed(self, client):
        """Test replay dead letter rejects GET requests."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="payments",
            message_type="PaymentFailed",
            payload={"order_id": str(uuid.uuid4())},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )
        response = client.get(f"/dead-letters/{dead_letter.id}/replay/")
        assert response.status_code == 405

    def test_discard_dead_letter_success(self, client):
        """Test discarding a dead letter successfully."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="payments",
            message_type="PaymentFailed",
            payload={"order_id": str(uuid.uuid4())},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )

        response = client.post(f"/dead-letters/{dead_letter.id}/discard/", data={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify status was updated
        dead_letter.refresh_from_db()
        assert dead_letter.status == DeadLetterMessage.Status.DISCARDED

    def test_discard_dead_letter_not_found(self, client):
        """Test discarding non-existent dead letter."""
        response = client.post(f"/dead-letters/{uuid.uuid4()}/discard/", data={})
        assert response.status_code == 404

    def test_discard_dead_letter_method_not_allowed(self, client):
        """Test discard dead letter rejects GET requests."""
        dead_letter = DeadLetterMessage.objects.create(
            id=uuid.uuid4(),
            queue_name="payments",
            message_type="PaymentFailed",
            payload={"order_id": str(uuid.uuid4())},
            error_message="Test error",
            correlation_id=uuid.uuid4(),
            status=DeadLetterMessage.Status.PENDING,
        )
        response = client.get(f"/dead-letters/{dead_letter.id}/discard/")
        assert response.status_code == 405


@pytest.mark.django_db
class TestNPlusOneQueries:
    """Test for N+1 query issues."""

    def test_orders_view_no_n_plus_one(self, client):
        """Test orders view doesn't have N+1 queries."""
        # Create test data
        for _ in range(5):
            order = Order.objects.create(
                id=uuid.uuid4(),
                customer_id=uuid.uuid4(),
                total_amount=100.00,
                status=Order.Status.PENDING,
            )
            OrderItem.objects.create(
                id=uuid.uuid4(),
                order=order,
                product_id=uuid.uuid4(),
                quantity=1,
                unit_price=100.00,
                total_price=100.00,
            )

        with CaptureQueriesContext(connection) as queries:
            response = client.get("/orders/")

        # Should not execute more than 2 queries (one for orders, maybe one for limit)
        assert len(queries) <= 2
        assert response.status_code == 200

    def test_order_detail_view_no_n_plus_one(self, client):
        """Test order detail view doesn't have N+1 queries."""
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            total_amount=100.00,
            status=Order.Status.PENDING,
        )

        # Create outbox messages
        for _ in range(5):
            OutboxMessage.objects.create(
                id=uuid.uuid4(),
                aggregate_id=order.id,
                aggregate_type="Order",
                message_type="OrderCreated",
                payload={"order_id": str(order.id)},
                correlation_id=uuid.uuid4(),
            )

        with CaptureQueriesContext(connection) as queries:
            response = client.get(f"/orders/{order.id}/")

        # Should not execute more than 8 queries (order, outbox messages, etc.)
        assert len(queries) <= 8
        assert response.status_code == 200

    def test_dead_letters_view_no_n_plus_one(self, client):
        """Test dead letters view doesn't have N+1 queries."""
        for _ in range(5):
            DeadLetterMessage.objects.create(
                id=uuid.uuid4(),
                queue_name="payments",
                message_type="PaymentFailed",
                payload={"order_id": str(uuid.uuid4())},
                error_message="Test error",
                correlation_id=uuid.uuid4(),
                status=DeadLetterMessage.Status.PENDING,
            )

        with CaptureQueriesContext(connection) as queries:
            response = client.get("/dead-letters/")

        # Should not execute more than 3 queries
        assert len(queries) <= 3
        assert response.status_code == 200

    def test_overview_view_no_n_plus_one(self, client):
        """Test overview view doesn't have N+1 queries."""
        # Create test data
        for _ in range(5):
            Order.objects.create(
                id=uuid.uuid4(),
                customer_id=uuid.uuid4(),
                total_amount=100.00,
                status=Order.Status.PENDING,
            )

        with CaptureQueriesContext(connection) as queries:
            response = client.get("/")

        # Should not execute more than 5 queries (counts, aggregates, etc.)
        assert len(queries) <= 5
        assert response.status_code == 200
