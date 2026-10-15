"""Management command to relay outbox messages to RabbitMQ."""

import json
from datetime import datetime

import pika
import structlog
from django.core.management.base import BaseCommand

from apps.messaging.messages import deserialize_message, serialize_message
from apps.outbox.services import get_pending_messages, mark_message_failed, mark_message_published

logger = structlog.get_logger(__name__)

# Routing key mapping for message types
ROUTING_KEYS: dict[str, str] = {
    "OrderCreated": "order.ordercreated",
    "OrderCancelled": "order.ordercancelled",
    "OrderConfirmed": "order.orderconfirmed",
    "OrderFailed": "order.orderfailed",
    "StockReserved": "inventory.stockreserved",
    "StockReservationFailed": "inventory.stockreservationfailed",
    "StockReleased": "inventory.stockreleased",
    "PaymentProcessed": "payments.paymentprocessed",
    "PaymentFailed": "payments.paymentfailed",
    "PaymentRefunded": "payments.paymentrefunded",
    "NotificationSent": "notifications.notificationsent",
}


class Command(BaseCommand):
    """Relay outbox messages to RabbitMQ."""

    help = "Relay pending outbox messages to RabbitMQ"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of messages to process",
        )
        parser.add_argument(
            "--rabbitmq-url",
            type=str,
            default="amqp://guest:guest@localhost:5672/%2F",
            help="RabbitMQ connection URL",
        )

    def handle(self, *args, **options) -> None:
        """Execute the relay command."""
        limit = options["limit"]
        rabbitmq_url = options["rabbitmq_url"]

        logger.info("Starting outbox relay", limit=limit, rabbitmq_url=rabbitmq_url)

        try:
            parameters = pika.URLParameters(rabbitmq_url)
            parameters.heartbeat = 600
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Declare exchange
            channel.exchange_declare(
                exchange="orquestra",
                exchange_type="topic",
                durable=True,
            )

            messages = get_pending_messages(limit=limit)

            if not messages:
                logger.info("No pending messages to relay")
                return

            published_count = 0
            failed_count = 0

            for message in messages:
                try:
                    # Deserialize and validate message
                    msg_obj = deserialize_message(message.message_type, message.payload)
                    serialized = serialize_message(msg_obj)

                    # Get routing key from mapping
                    routing_key = ROUTING_KEYS.get(message.message_type)
                    if routing_key is None:
                        logger.error(
                            "Unknown message type",
                            message_type=message.message_type,
                        )
                        mark_message_failed(
                            message.id, f"Unknown message type: {message.message_type}"
                        )
                        failed_count += 1
                        continue

                    # Publish to RabbitMQ
                    channel.basic_publish(
                        exchange="orquestra",
                        routing_key=routing_key,
                        body=json.dumps(serialized),
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # Make message persistent
                            message_id=str(message.id),
                            timestamp=int(datetime.now().timestamp()),
                            correlation_id=str(message.correlation_id),
                        ),
                    )

                    # Mark as published
                    mark_message_published(message.id)
                    published_count += 1

                    logger.info(
                        "Message published",
                        message_id=str(message.id),
                        message_type=message.message_type,
                        routing_key=routing_key,
                    )

                except Exception as e:
                    # Mark as failed
                    mark_message_failed(message.id, str(e))
                    failed_count += 1

                    logger.error(
                        "Failed to publish message",
                        message_id=str(message.id),
                        message_type=message.message_type,
                        error=str(e),
                    )

            connection.close()

            logger.info(
                "Relay completed",
                published=published_count,
                failed=failed_count,
                total=len(messages),
            )

        except Exception as e:
            logger.error("Relay failed", error=str(e))
            self.stderr.write(self.style.ERROR(f"Relay failed: {e}"))
            raise
