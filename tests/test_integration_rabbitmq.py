"""Integration tests with real RabbitMQ.

Note: These tests require RabbitMQ to be running locally.
Run with: docker compose --profile lite up -d
Skip with: pytest -m "not integration"
"""

import json
import uuid
from datetime import datetime
from decimal import Decimal

import pika
import pytest
from django.test import TestCase

from apps.messaging.messages import OrderCreated, OrderItemMessage, serialize_message
from apps.orders.services import create_order
from apps.outbox.services import create_outbox_message

pytestmark = pytest.mark.integration


class RabbitMQIntegrationTests(TestCase):
    """Integration tests with real RabbitMQ."""

    def setUp(self) -> None:
        """Set up RabbitMQ connection for tests."""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters("amqp://guest:guest@localhost:5672/%2F")
            )
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange="orquestra",
                exchange_type="topic",
                durable=True,
            )

            # Declare queues
            for queue_name in ["inventory", "payments", "notifications", "audit", "orchestrator"]:
                self.channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments={"x-queue-type": "quorum"},
                )
        except Exception:
            self.skipTest("RabbitMQ not available")

    def tearDown(self) -> None:
        """Close RabbitMQ connection."""
        if hasattr(self, "connection"):
            self.connection.close()

    def test_outbox_message_created(self) -> None:
        """Test that outbox message is created when order is created."""
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": uuid.uuid4(),
                "quantity": 2,
                "unit_price": "10.50",
            }
        ]

        order = create_order(customer_id, items)

        # Check that outbox message was created
        from apps.outbox.models import OutboxMessage

        outbox_messages = OutboxMessage.objects.filter(aggregate_id=order.id)
        assert outbox_messages.count() == 1
        first_message = outbox_messages.first()
        assert first_message is not None
        assert first_message.message_type == "OrderCreated"
        assert first_message.status == "PENDING"

    def test_relay_publishes_to_rabbitmq(self) -> None:
        """Test that relay publishes messages to RabbitMQ."""
        # Create an outbox message
        correlation_id = uuid.uuid4()
        order_id = uuid.uuid4()
        order_created = OrderCreated(
            correlation_id=correlation_id,
            causation_id=None,
            timestamp=datetime.now().isoformat(),
            order_id=order_id,
            customer_id=uuid.uuid4(),
            total_amount=Decimal("21.00"),
            items=[
                OrderItemMessage(
                    product_id=uuid.uuid4(),
                    quantity=2,
                    unit_price=Decimal("10.50"),
                )
            ],
        )

        create_outbox_message(
            message_type="OrderCreated",
            payload=order_created.model_dump(mode="json"),
            aggregate_type="order",
            aggregate_id=order_id,
            correlation_id=correlation_id,
            causation_id=None,
        )

        # Run relay
        from django.core.management import call_command

        call_command("relay", limit=10, rabbitmq_url="amqp://guest:guest@localhost:5672/%2F")

        # Check that message was marked as published
        from apps.outbox.models import OutboxMessage

        outbox_message = OutboxMessage.objects.get(aggregate_id=order_id)
        assert outbox_message.status == "PUBLISHED"
        assert outbox_message.published_at is not None

    def test_message_routing(self) -> None:
        """Test that messages are routed to correct queues."""
        # Create an OrderCreated message
        correlation_id = uuid.uuid4()
        order_id = uuid.uuid4()
        order_created = OrderCreated(
            correlation_id=correlation_id,
            causation_id=None,
            timestamp=datetime.now().isoformat(),
            order_id=order_id,
            customer_id=uuid.uuid4(),
            total_amount=Decimal("21.00"),
            items=[
                OrderItemMessage(
                    product_id=uuid.uuid4(),
                    quantity=2,
                    unit_price=Decimal("10.50"),
                )
            ],
        )

        # Publish to RabbitMQ
        self.channel.basic_publish(
            exchange="orquestra",
            routing_key="order.ordercreated",
            body=json.dumps(serialize_message(order_created)),
            properties=pika.BasicProperties(
                delivery_mode=2,
                message_id=str(correlation_id),
                correlation_id=str(correlation_id),
            ),
        )

        # Check that message was routed to inventory queue
        method_frame, header_frame, body = self.channel.basic_get(queue="inventory")
        assert method_frame is not None
        message = json.loads(body)
        assert message["message_type"] == "OrderCreated"
