"""Setup RabbitMQ queues, exchanges and bindings."""

import pika

RABBITMQ_URL = "amqp://guest:guest@localhost:5672/%2F"

# Queue definitions
QUEUES = [
    "inventory",
    "payments",
    "notifications",
    "audit",
    "orchestrator",
    "inventory.dlq",
    "payments.dlq",
    "notifications.dlq",
    "audit.dlq",
    "orchestrator.dlq",
]

# Exchange definitions
EXCHANGES = [
    {"name": "orquestra", "type": "topic", "durable": True},
    {"name": "orquestra.dlx", "type": "direct", "durable": True},
]

# Binding definitions
BINDINGS = [
    {"source": "orquestra", "destination": "inventory", "routing_key": "order.ordercreated"},
    {"source": "orquestra", "destination": "payments", "routing_key": "inventory.stockreserved"},
    {
        "source": "orquestra",
        "destination": "notifications",
        "routing_key": "payments.paymentprocessed",
    },
    {
        "source": "orquestra",
        "destination": "notifications",
        "routing_key": "payments.paymentfailed",
    },
    {
        "source": "orquestra",
        "destination": "orchestrator",
        "routing_key": "payments.paymentprocessed",
    },
    {"source": "orquestra", "destination": "orchestrator", "routing_key": "payments.paymentfailed"},
    {
        "source": "orquestra",
        "destination": "orchestrator",
        "routing_key": "inventory.stockreservationfailed",
    },
    {"source": "orquestra", "destination": "audit", "routing_key": "order.*"},
    {"source": "orquestra", "destination": "audit", "routing_key": "inventory.*"},
    {"source": "orquestra", "destination": "audit", "routing_key": "payments.*"},
    {"source": "orquestra", "destination": "audit", "routing_key": "notifications.*"},
    {"source": "orquestra.dlx", "destination": "inventory.dlq", "routing_key": "inventory.dlq"},
    {"source": "orquestra.dlx", "destination": "payments.dlq", "routing_key": "payments.dlq"},
    {
        "source": "orquestra.dlx",
        "destination": "notifications.dlq",
        "routing_key": "notifications.dlq",
    },
    {"source": "orquestra.dlx", "destination": "audit.dlq", "routing_key": "audit.dlq"},
    {
        "source": "orquestra.dlx",
        "destination": "orchestrator.dlq",
        "routing_key": "orchestrator.dlq",
    },
]


def setup_rabbitmq() -> None:
    """Setup RabbitMQ infrastructure."""
    print(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()

    # Declare exchanges
    for exchange in EXCHANGES:
        print(f"Declaring exchange: {exchange['name']}")
        channel.exchange_declare(
            exchange=exchange["name"],
            exchange_type=exchange["type"],
            durable=exchange["durable"],
        )

    # Declare queues
    for queue in QUEUES:
        print(f"Declaring queue: {queue}")
        if queue.endswith(".dlq"):
            channel.queue_declare(queue=queue, durable=True, arguments={"x-queue-type": "quorum"})
        else:
            channel.queue_declare(
                queue=queue,
                durable=True,
                arguments={
                    "x-queue-type": "quorum",
                    "x-dead-letter-exchange": "orquestra.dlx",
                    "x-dead-letter-routing-key": f"{queue}.dlq",
                },
            )

    # Declare bindings
    for binding in BINDINGS:
        print(
            f"Binding {binding['source']} -> {binding['destination']} with routing_key={binding['routing_key']}"
        )
        channel.queue_bind(
            queue=binding["destination"],
            exchange=binding["source"],
            routing_key=binding["routing_key"],
        )

    connection.close()
    print("RabbitMQ setup completed successfully!")


if __name__ == "__main__":
    setup_rabbitmq()
