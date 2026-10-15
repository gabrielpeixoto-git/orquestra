"""RabbitMQ consumer that dispatches to Celery task handlers."""

import io
import json
import os
import sys

import pika
import structlog

# Fix Windows encoding issue
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django

django.setup()

from apps.messaging.messages import deserialize_message

logger = structlog.get_logger(__name__)

# Queue to message type handlers mapping
QUEUE_HANDLERS = {
    "inventory": {
        "OrderCreated": ["apps.inventory.tasks.handlers.handle_order_created"],
    },
    "payments": {
        "StockReserved": ["apps.payments.tasks.handlers.handle_stock_reserved"],
    },
    "notifications": {
        "PaymentProcessed": ["apps.notifications.tasks.handlers.handle_payment_processed"],
        "OrderConfirmed": ["apps.notifications.tasks.handlers.handle_order_confirmed"],
        "OrderFailed": ["apps.notifications.tasks.handlers.handle_order_failed"],
    },
    "audit": {
        "OrderCreated": ["apps.audit.tasks.handlers.handle_all_messages"],
        "StockReserved": ["apps.audit.tasks.handlers.handle_all_messages"],
        "StockReservationFailed": ["apps.audit.tasks.handlers.handle_all_messages"],
        "PaymentProcessed": ["apps.audit.tasks.handlers.handle_all_messages"],
        "PaymentFailed": ["apps.audit.tasks.handlers.handle_all_messages"],
        "OrderConfirmed": ["apps.audit.tasks.handlers.handle_all_messages"],
        "OrderFailed": ["apps.audit.tasks.handlers.handle_all_messages"],
        "NotificationSent": ["apps.audit.tasks.handlers.handle_all_messages"],
    },
    "orchestrator": {
        "PaymentProcessed": ["apps.orchestrator.tasks.handlers.handle_payment_processed"],
        "PaymentFailed": ["apps.orchestrator.tasks.handlers.handle_payment_failed"],
        "StockReservationFailed": [
            "apps.orchestrator.tasks.handlers.handle_stock_reservation_failed"
        ],
    },
}


def create_callback(queue_name):
    """Create a callback function for the given queue."""

    def inner_callback(ch, method, _properties, body):
        try:
            message_data = json.loads(body)
            logger.info(
                "Received message",
                queue=queue_name,
                routing_key=method.routing_key,
                message_type=message_data.get("message_type"),
            )

            # Deserialize message
            message_type = message_data.get("message_type")
            if message_type:
                msg_obj = deserialize_message(message_type, message_data)
                payload = msg_obj.model_dump(mode="json")
            else:
                payload = message_data

            # Find handlers for this queue and message type
            queue_handlers = QUEUE_HANDLERS.get(queue_name, {})
            handler_paths = queue_handlers.get(message_type, [])

            if not handler_paths:
                logger.warning(
                    "No handler for queue/message type",
                    queue=queue_name,
                    message_type=message_type,
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Call all handlers for this message type
            for handler_path in handler_paths:
                try:
                    # Import and call handler
                    module_path, func_name = handler_path.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[func_name])
                    handler_func = getattr(module, func_name)

                    # Call handler with appropriate parameters
                    if "handle_all_messages" in func_name:
                        handler_func(payload, message_type)
                    else:
                        handler_func(payload)

                    logger.info(
                        "Handler executed successfully",
                        handler=func_name,
                        message_type=message_type,
                    )
                except Exception as handler_error:
                    logger.exception(
                        "Handler failed",
                        handler=func_name,
                        message_type=message_type,
                        error=str(handler_error),
                    )
                    # Continue with other handlers even if one fails

            logger.info(
                "Message processed successfully",
                queue=queue_name,
                message_type=message_type,
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.exception(
                "Failed to process message",
                queue=queue_name,
                error=str(e),
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    return inner_callback


def consume_messages(queue_name: str) -> None:
    """Consume messages from a specific queue."""
    connection = pika.BlockingConnection(
        pika.URLParameters("amqp://guest:guest@localhost:5672/%2F")
    )
    channel = connection.channel()

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=create_callback(queue_name),
    )

    logger.info("Started consuming from queue", queue=queue_name)
    channel.start_consuming()


if __name__ == "__main__":
    queue_name = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    consume_messages(queue_name)
