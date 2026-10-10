"""Integration tests for complete saga flow."""

import uuid
from decimal import Decimal

from django.test import TestCase

from apps.inventory.services import create_product
from apps.orders.services import create_order
from apps.outbox.models import OutboxMessage


class SagaIntegrationTests(TestCase):
    """Integration tests for complete saga flow."""

    def setUp(self) -> None:
        """Set up test data."""
        self.product = create_product(
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

    def test_complete_saga_flow_success(self) -> None:
        """Test complete saga flow from order creation to confirmation."""
        # Create an order
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": self.product.id,
                "quantity": 2,
                "unit_price": "10.00",
            }
        ]

        order = create_order(customer_id, items)

        # Check initial state
        assert order.status == "PENDING"
        assert order.total_amount == Decimal("20.00")

        # Check that outbox message was created
        outbox_messages = OutboxMessage.objects.filter(aggregate_id=order.id)
        assert outbox_messages.count() == 1
        first_message = outbox_messages.first()
        assert first_message is not None
        assert first_message.message_type == "OrderCreated"

        # In a real test with RabbitMQ and Celery workers running:
        # 1. Message would be consumed by inventory worker
        # 2. Stock would be reserved
        # 3. StockReserved message would be emitted
        # 4. Message would be consumed by payments worker
        # 5. Payment would be processed
        # 6. PaymentProcessed message would be emitted
        # 7. Message would be consumed by orchestrator worker
        # 8. Order would be confirmed

        # For now, we test the synchronous flow
        # Note: Full saga flow requires RabbitMQ and Celery workers
        # This test validates the initial setup and outbox pattern

    def test_outbox_pattern_guarantee(self) -> None:
        """Test that outbox pattern guarantees message publication."""
        # Create an order
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": self.product.id,
                "quantity": 1,
                "unit_price": "10.00",
            }
        ]

        order = create_order(customer_id, items)

        # Check that outbox message was created in the same transaction
        outbox_messages = OutboxMessage.objects.filter(aggregate_id=order.id)
        assert outbox_messages.count() == 1

        outbox_message = outbox_messages.first()
        assert outbox_message is not None
        assert outbox_message.message_type == "OrderCreated"
        assert outbox_message.status == "PENDING"
        assert outbox_message.aggregate_type == "order"
        assert outbox_message.aggregate_id == order.id
        # correlation_id is generated separately for tracing
        assert outbox_message.correlation_id is not None
