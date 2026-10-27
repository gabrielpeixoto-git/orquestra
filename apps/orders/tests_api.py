"""Tests for orders API endpoints."""

import uuid
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem


class CreateOrderAPITests(TestCase):
    """Tests for POST /api/v1/orders/ endpoint."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = APIClient()

    def test_create_order_success(self) -> None:
        """Test creating an order via API."""
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()
        data = {
            "customer_id": str(customer_id),
            "items": [
                {
                    "product_id": str(product_id),
                    "quantity": 2,
                    "unit_price": "10.50",
                }
            ],
        }

        response = self.client.post("/api/v1/orders/", data, format="json")

        assert response.status_code == 201
        assert response.data["customer_id"] == str(customer_id)
        assert response.data["status"] == Order.Status.PENDING
        assert len(response.data["items"]) == 1

    def test_create_order_with_multiple_items(self) -> None:
        """Test creating an order with multiple items via API."""
        customer_id = uuid.uuid4()
        data = {
            "customer_id": str(customer_id),
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 2,
                    "unit_price": "10.00",
                },
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 1,
                    "unit_price": "5.00",
                },
            ],
        }

        response = self.client.post("/api/v1/orders/", data, format="json")

        assert response.status_code == 201
        assert len(response.data["items"]) == 2
        assert response.data["total_amount"] == "25.00"

    def test_create_order_with_empty_items_raises_error(self) -> None:
        """Test creating an order with empty items list raises error."""
        customer_id = uuid.uuid4()
        data = {
            "customer_id": str(customer_id),
            "items": [],
        }

        response = self.client.post("/api/v1/orders/", data, format="json")

        assert response.status_code == 400

    def test_create_order_with_invalid_quantity_raises_error(self) -> None:
        """Test creating an order with invalid quantity raises error."""
        customer_id = uuid.uuid4()
        data = {
            "customer_id": str(customer_id),
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 0,
                    "unit_price": "10.00",
                }
            ],
        }

        response = self.client.post("/api/v1/orders/", data, format="json")

        assert response.status_code == 400

    def test_create_order_with_invalid_price_raises_error(self) -> None:
        """Test creating an order with invalid price raises error."""
        customer_id = uuid.uuid4()
        data = {
            "customer_id": str(customer_id),
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 1,
                    "unit_price": "0.00",
                }
            ],
        }

        response = self.client.post("/api/v1/orders/", data, format="json")

        assert response.status_code == 400

    def test_create_order_with_invalid_data_raises_creation_error(self) -> None:
        """Test creating an order with invalid data raises OrderCreationError."""
        from unittest.mock import patch

        from apps.orders.services import OrderCreationError

        customer_id = uuid.uuid4()
        data = {
            "customer_id": str(customer_id),
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 1,
                    "unit_price": "10.00",
                }
            ],
        }

        with patch("apps.orders.views.create_order", side_effect=OrderCreationError("DB error")):
            response = self.client.post("/api/v1/orders/", data, format="json")

        assert response.status_code == 400

    def test_create_order_with_serializer_error(self) -> None:
        """Test creating an order with invalid serializer data."""
        data = {
            "customer_id": "invalid-uuid",
            "items": [],
        }

        response = self.client.post("/api/v1/orders/", data, format="json")

        assert response.status_code == 400


class OrderDetailAPITests(TestCase):
    """Tests for GET /api/v1/orders/<uuid>/ endpoint."""

    def setUp(self) -> None:
        """Set up test client and order."""
        self.client = APIClient()
        self.order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            customer_name="Test Customer",
            total_amount=Decimal("100.00"),
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            id=uuid.uuid4(),
            order=self.order,
            product_id=uuid.uuid4(),
            quantity=2,
            unit_price=Decimal("50.00"),
            total_price=Decimal("100.00"),
        )

    def test_get_order_success(self) -> None:
        """Test getting an order via API."""
        response = self.client.get(f"/api/v1/orders/{self.order.id}/")

        assert response.status_code == 200
        assert response.data["id"] == str(self.order.id)
        assert response.data["status"] == Order.Status.PENDING
        assert len(response.data["items"]) == 1

    def test_get_nonexistent_order_returns_404(self) -> None:
        """Test getting a non-existent order returns 404."""
        order_id = uuid.uuid4()
        response = self.client.get(f"/api/v1/orders/{order_id}/")

        assert response.status_code == 404

    def test_get_order_with_invalid_uuid(self) -> None:
        """Test getting an order with invalid UUID."""
        response = self.client.get("/api/v1/orders/invalid-uuid/")

        assert response.status_code == 404
