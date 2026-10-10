"""Management command to replay dead letter messages."""

import json

import pika
import structlog
from django.core.management.base import BaseCommand

from apps.outbox.services_deadletter import get_pending_dead_letters, mark_dead_letter_replayed

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Replay dead letter messages to RabbitMQ."""

    help = "Replay dead letter messages to RabbitMQ"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--queue",
            type=str,
            default=None,
            help="Queue name to filter messages (optional)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of messages to replay",
        )
        parser.add_argument(
            "--rabbitmq-url",
            type=str,
            default="amqp://guest:guest@localhost:5672/%2F",
            help="RabbitMQ connection URL",
        )

    def handle(self, *args, **options) -> None:
        """Execute the replay command."""
        queue_name = options["queue"]
        limit = options["limit"]
        rabbitmq_url = options["rabbitmq_url"]

        logger.info("Starting DLQ replay", queue=queue_name, limit=limit, rabbitmq_url=rabbitmq_url)

        try:
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            channel = connection.channel()

            # Declare exchange
            channel.exchange_declare(
                exchange="orquestra",
                exchange_type="topic",
                durable=True,
            )

            messages = get_pending_dead_letters(queue_name=queue_name, limit=limit)

            if not messages:
                logger.info("No pending dead letter messages to replay")
                return

            replayed_count = 0

            for message in messages:
                try:
                    # Publish to RabbitMQ
                    routing_key = f"{message.queue_name}.{message.message_type.lower()}"
                    channel.basic_publish(
                        exchange="orquestra",
                        routing_key=routing_key,
                        body=json.dumps(message.payload),
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            message_id=str(message.id),
                            correlation_id=str(message.correlation_id),
                        ),
                    )

                    # Mark as replayed
                    mark_dead_letter_replayed(message.id)
                    replayed_count += 1

                    logger.info(
                        "Message replayed",
                        message_id=str(message.id),
                        queue_name=message.queue_name,
                        message_type=message.message_type,
                    )

                except Exception as e:
                    logger.exception(
                        "Failed to replay message",
                        message_id=str(message.id),
                        error=str(e),
                    )

            connection.close()

            logger.info(
                "DLQ replay completed",
                replayed=replayed_count,
                total=len(messages),
            )

        except Exception as e:
            logger.exception("DLQ replay failed")
            self.stderr.write(self.style.ERROR(f"DLQ replay failed: {e}"))
            raise
