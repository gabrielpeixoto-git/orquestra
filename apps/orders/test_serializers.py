"""Tests for orders serializers."""

import uuid

from apps.orders.serializers import (
    CreateOrderSerializer,
    OrderItemSerializer,
)


def test_order_item_serializer_valid() -> None:
    """Test OrderItemSerializer with valid data."""
    data = {
        "product_id": str(uuid.uuid4()),
        "quantity": 2,
        "unit_price": "100.00",
    }
    serializer = OrderItemSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data["quantity"] == 2


def test_order_item_serializer_invalid_quantity() -> None:
    """Test OrderItemSerializer with invalid quantity."""
    data = {
        "product_id": str(uuid.uuid4()),
        "quantity": 0,
        "unit_price": "100.00",
    }
    serializer = OrderItemSerializer(data=data)
    assert not serializer.is_valid()
    assert "quantity" in serializer.errors


def test_order_item_serializer_invalid_price() -> None:
    """Test OrderItemSerializer with invalid price."""
    data = {
        "product_id": str(uuid.uuid4()),
        "quantity": 1,
        "unit_price": "0.00",
    }
    serializer = OrderItemSerializer(data=data)
    assert not serializer.is_valid()
    assert "unit_price" in serializer.errors


def test_create_order_serializer_valid() -> None:
    """Test CreateOrderSerializer with valid data."""
    data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "unit_price": "100.00",
            }
        ],
    }
    serializer = CreateOrderSerializer(data=data)
    assert serializer.is_valid()


def test_create_order_serializer_empty_items() -> None:
    """Test CreateOrderSerializer with empty items list."""
    data = {
        "customer_id": str(uuid.uuid4()),
        "items": [],
    }
    serializer = CreateOrderSerializer(data=data)
    assert not serializer.is_valid()
    assert "items" in serializer.errors
    assert "At least one item is required" in str(serializer.errors["items"])


def test_create_order_serializer_invalid_uuid() -> None:
    """Test CreateOrderSerializer with invalid customer_id."""
    data = {
        "customer_id": "invalid-uuid",
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "unit_price": "100.00",
            }
        ],
    }
    serializer = CreateOrderSerializer(data=data)
    assert not serializer.is_valid()
    assert "customer_id" in serializer.errors
