"""Tests for messaging contracts."""

import uuid
from decimal import Decimal

import pytest

from apps.messaging.messages import (
    OrderCreated,
    OrderItemMessage,
    StockReserved,
    deserialize_message,
    serialize_message,
)


def test_serialize_message() -> None:
    """Test message serialization."""
    message = OrderCreated(
        correlation_id=uuid.uuid4(),
        timestamp="2024-01-01T00:00:00Z",
        order_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        total_amount=Decimal("100.00"),
        items=[
            OrderItemMessage(
                product_id=uuid.uuid4(),
                quantity=2,
                unit_price=Decimal("50.00"),
            )
        ],
    )

    serialized = serialize_message(message)

    assert isinstance(serialized, dict)
    assert "correlation_id" in serialized
    assert "order_id" in serialized
    assert serialized["message_type"] == "OrderCreated"


def test_deserialize_message() -> None:
    """Test message deserialization."""
    payload = {
        "correlation_id": str(uuid.uuid4()),
        "timestamp": "2024-01-01T00:00:00Z",
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "total_amount": "100.00",
        "items": [],
    }

    message = deserialize_message("OrderCreated", payload)

    assert isinstance(message, OrderCreated)
    assert message.order_id == uuid.UUID(payload["order_id"])


def test_deserialize_unknown_message_type() -> None:
    """Test deserializing unknown message type raises ValueError."""
    payload = {"test": "data"}

    with pytest.raises(ValueError, match="Unknown message type"):
        deserialize_message("UnknownMessage", payload)


def test_serialize_stock_reserved() -> None:
    """Test StockReserved message serialization."""
    message = StockReserved(
        correlation_id=uuid.uuid4(),
        timestamp="2024-01-01T00:00:00Z",
        order_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        quantity=5,
        reservation_id=uuid.uuid4(),
    )

    serialized = serialize_message(message)

    assert serialized["quantity"] == 5
    assert "reservation_id" in serialized
