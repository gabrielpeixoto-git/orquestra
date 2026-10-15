"""Message contracts using pydantic v2."""

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    """Base message with common fields."""

    correlation_id: uuid.UUID = Field(..., description="Correlation ID for tracing")
    causation_id: uuid.UUID | None = Field(None, description="Causation ID for message chain")
    timestamp: str = Field(..., description="Message timestamp in ISO format")


class OrderItemMessage(BaseModel):
    """Order item in message."""

    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal


class OrderCreated(BaseMessage):
    """Message emitted when an order is created."""

    order_id: uuid.UUID
    customer_id: uuid.UUID
    total_amount: Decimal
    items: list[OrderItemMessage]


class OrderCancelled(BaseMessage):
    """Message emitted when an order is cancelled."""

    order_id: uuid.UUID
    customer_id: uuid.UUID
    reason: str | None = None


class StockReserved(BaseMessage):
    """Message emitted when stock is reserved."""

    order_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    reservation_id: uuid.UUID


class StockReservationFailed(BaseMessage):
    """Message emitted when stock reservation fails."""

    order_id: uuid.UUID
    product_id: uuid.UUID
    requested_quantity: int
    available_quantity: int
    reason: str


class StockReleased(BaseMessage):
    """Message emitted when stock is released."""

    order_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    reservation_id: uuid.UUID


class PaymentProcessed(BaseMessage):
    """Message emitted when payment is processed successfully."""

    order_id: uuid.UUID
    payment_id: uuid.UUID
    amount: Decimal
    gateway_transaction_id: str


class PaymentFailed(BaseMessage):
    """Message emitted when payment fails."""

    order_id: uuid.UUID
    amount: Decimal
    reason: str


class PaymentRefunded(BaseMessage):
    """Message emitted when payment is refunded."""

    order_id: uuid.UUID
    payment_id: uuid.UUID
    amount: Decimal


class NotificationSent(BaseMessage):
    """Message emitted when notification is sent."""

    notification_id: uuid.UUID
    recipient: str
    notification_type: str
    subject: str


class OrderConfirmed(BaseMessage):
    """Message emitted when order is confirmed."""

    order_id: uuid.UUID
    customer_id: uuid.UUID
    total_amount: Decimal


class OrderFailed(BaseMessage):
    """Message emitted when order fails."""

    order_id: uuid.UUID
    customer_id: uuid.UUID
    reason: str
    failure_step: str


# Message type mapping for serialization
MESSAGE_TYPES: dict[str, type[BaseMessage]] = {
    "OrderCreated": OrderCreated,
    "OrderCancelled": OrderCancelled,
    "StockReserved": StockReserved,
    "StockReservationFailed": StockReservationFailed,
    "StockReleased": StockReleased,
    "PaymentProcessed": PaymentProcessed,
    "PaymentFailed": PaymentFailed,
    "PaymentRefunded": PaymentRefunded,
    "NotificationSent": NotificationSent,
    "OrderConfirmed": OrderConfirmed,
    "OrderFailed": OrderFailed,
}


def serialize_message(message: BaseMessage) -> dict[str, Any]:
    """Serialize a message to dictionary.

    Args:
        message: Message to serialize.

    Returns:
        Serialized message as dictionary with message_type included.
    """
    payload = message.model_dump(mode="json")
    payload["message_type"] = message.__class__.__name__
    return payload


def deserialize_message(message_type: str, payload: dict[str, Any]) -> BaseMessage:
    """Deserialize a message from dictionary.

    Args:
        message_type: Type of the message.
        payload: Serialized message payload.

    Returns:
        Deserialized message instance.

    Raises:
        ValueError: If message type is unknown.
    """
    message_class = MESSAGE_TYPES.get(message_type)
    if message_class is None:
        error_msg = f"Unknown message type: {message_type}"
        raise ValueError(error_msg)

    # Remove message_type from payload if present (it's metadata, not a field)
    clean_payload = {k: v for k, v in payload.items() if k != "message_type"}
    return message_class(**clean_payload)
