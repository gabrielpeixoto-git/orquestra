"""Management command to seed demo data."""

import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    """Seed demo data for testing."""

    help = "Seed realistic demo data simulating months of usage"

    def handle(self, *args, **options) -> None:
        """Execute the seed command."""
        from apps.audit.models import AuditLog
        from apps.inventory.models import Product, StockReservation
        from apps.orders.models import Order, OrderItem
        from apps.outbox.models import DeadLetterMessage, OutboxMessage
        from apps.payments.models import Payment

        print("Seeding realistic demo data...")

        # Clear existing data
        AuditLog.objects.all().delete()
        OutboxMessage.objects.all().delete()
        DeadLetterMessage.objects.all().delete()
        StockReservation.objects.all().delete()
        Payment.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()

        # Create realistic products
        products_data = [
            {
                "name": "Laptop Pro 15",
                "description": "High-performance laptop with 16GB RAM and 512GB SSD",
                "price": Decimal("1299.99"),
                "stock_quantity": 45,
            },
            {
                "name": "Wireless Mouse",
                "description": "Ergonomic wireless mouse with precision tracking",
                "price": Decimal("29.99"),
                "stock_quantity": 200,
            },
            {
                "name": "USB-C Hub",
                "description": "7-in-1 USB-C hub with HDMI and SD card reader",
                "price": Decimal("49.99"),
                "stock_quantity": 150,
            },
            {
                "name": "Mechanical Keyboard",
                "description": "RGB mechanical keyboard with Cherry MX switches",
                "price": Decimal("149.99"),
                "stock_quantity": 80,
            },
            {
                "name": '27" 4K Monitor',
                "description": "Ultra HD monitor with HDR support",
                "price": Decimal("399.99"),
                "stock_quantity": 35,
            },
            {
                "name": "Webcam HD",
                "description": "1080p webcam with auto-focus and built-in mic",
                "price": Decimal("79.99"),
                "stock_quantity": 120,
            },
            {
                "name": "Docking Station",
                "description": "Universal laptop docking station",
                "price": Decimal("189.99"),
                "stock_quantity": 60,
            },
            {
                "name": "External SSD 1TB",
                "description": "Portable SSD with USB 3.2 Gen 2",
                "price": Decimal("159.99"),
                "stock_quantity": 90,
            },
            {
                "name": "Desk Lamp LED",
                "description": "Adjustable LED desk lamp with wireless charging",
                "price": Decimal("59.99"),
                "stock_quantity": 180,
            },
            {
                "name": "Ergonomic Chair",
                "description": "Office chair with lumbar support",
                "price": Decimal("349.99"),
                "stock_quantity": 25,
            },
        ]

        products = []
        for product_data in products_data:
            product = Product.objects.create(
                id=uuid.uuid4(),
                **product_data,
            )
            products.append(product)
            print(f"Created product: {product.name} (ID: {product.id})")

        # Generate orders over the last 3 months
        now = timezone.now()
        three_months_ago = now - timedelta(days=90)

        # Customer data (simulate recurring customers with real names)
        customer_data = [
            {"id": uuid.uuid4(), "name": "Ana Silva"},
            {"id": uuid.uuid4(), "name": "Bruno Santos"},
            {"id": uuid.uuid4(), "name": "Carla Oliveira"},
            {"id": uuid.uuid4(), "name": "Daniel Costa"},
            {"id": uuid.uuid4(), "name": "Elena Ferreira"},
            {"id": uuid.uuid4(), "name": "Felipe Mendes"},
            {"id": uuid.uuid4(), "name": "Gabriela Rodrigues"},
            {"id": uuid.uuid4(), "name": "Henrique Almeida"},
            {"id": uuid.uuid4(), "name": "Isabela Nunes"},
            {"id": uuid.uuid4(), "name": "João Pedro Souza"},
            {"id": uuid.uuid4(), "name": "Juliana Lima"},
            {"id": uuid.uuid4(), "name": "Lucas Araújo"},
            {"id": uuid.uuid4(), "name": "Mariana Rocha"},
            {"id": uuid.uuid4(), "name": "Nicolas Pinto"},
            {"id": uuid.uuid4(), "name": "Olávia Barbosa"},
            {"id": uuid.uuid4(), "name": "Paulo Ricardo"},
            {"id": uuid.uuid4(), "name": "Rafaela Cardoso"},
            {"id": uuid.uuid4(), "name": "Samuel Gomes"},
            {"id": uuid.uuid4(), "name": "Tatiana Martins"},
            {"id": uuid.uuid4(), "name": "Victor Hugo"},
        ]

        order_statuses = [
            Order.Status.CONFIRMED,
            Order.Status.CONFIRMED,
            Order.Status.CONFIRMED,
            Order.Status.CONFIRMED,
            Order.Status.CONFIRMED,
            Order.Status.CANCELLED,
            Order.Status.PENDING,
            Order.Status.STOCK_RESERVED,
            Order.Status.PAYMENT_SUCCEEDED,
        ]

        total_orders = 150
        for i in range(total_orders):
            # Random date within last 3 months
            days_ago = random.randint(0, 90)
            created_at = three_months_ago + timedelta(days=days_ago)
            updated_at = created_at + timedelta(minutes=random.randint(5, 60))

            # Random customer
            customer = random.choice(customer_data)
            customer_id = customer["id"]
            customer_name = customer["name"]

            # Random products and quantities
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, num_items)

            order = Order.objects.create(
                id=uuid.uuid4(),
                customer_id=customer_id,
                customer_name=customer_name,
                total_amount=Decimal("0.00"),
                status=random.choice(order_statuses),
                created_at=created_at,
                updated_at=updated_at,
            )

            total_amount = Decimal("0.00")
            for product in selected_products:
                quantity = random.randint(1, 5)
                unit_price = product.price
                total_price = unit_price * quantity
                total_amount += total_price

                OrderItem.objects.create(
                    id=uuid.uuid4(),
                    order=order,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )

            order.total_amount = total_amount
            order.save()

            # Create payment for non-pending orders
            if order.status != Order.Status.PENDING:
                payment_status = (
                    Payment.Status.SUCCEEDED
                    if order.status == Order.Status.CONFIRMED
                    else Payment.Status.FAILED
                )
                Payment.objects.create(
                    id=uuid.uuid4(),
                    order_id=order.id,
                    amount=total_amount,
                    status=payment_status,
                    gateway_transaction_id=f"txn_{uuid.uuid4().hex[:16]}",
                    created_at=created_at + timedelta(minutes=2),
                    updated_at=updated_at,
                )

            # Create stock reservation for orders that reached that stage
            if order.status in [
                Order.Status.STOCK_RESERVED,
                Order.Status.PAYMENT_SUCCEEDED,
                Order.Status.CONFIRMED,
            ]:
                for product in selected_products:
                    StockReservation.objects.create(
                        id=uuid.uuid4(),
                        order_id=order.id,
                        product_id=product.id,
                        quantity=random.randint(1, 5),
                        status=StockReservation.Status.CONFIRMED
                        if order.status == Order.Status.CONFIRMED
                        else StockReservation.Status.ACTIVE,
                        created_at=created_at + timedelta(minutes=1),
                        expires_at=created_at + timedelta(days=7),
                    )

            # Create audit logs
            AuditLog.objects.create(
                id=uuid.uuid4(),
                action=AuditLog.Action.ORDER_CREATED,
                actor="system",
                entity_type="Order",
                entity_id=order.id,
                changes={"total_amount": str(total_amount)},
                timestamp=created_at,
            )

            if order.status == Order.Status.CANCELLED:
                AuditLog.objects.create(
                    id=uuid.uuid4(),
                    action=AuditLog.Action.ORDER_CANCELLED,
                    actor="system",
                    entity_type="Order",
                    entity_id=order.id,
                    changes={"status": "CANCELLED"},
                    timestamp=updated_at,
                )

            # Create outbox messages
            correlation_id = uuid.uuid4()
            OutboxMessage.objects.create(
                id=uuid.uuid4(),
                message_type="OrderCreated",
                payload={
                    "order_id": str(order.id),
                    "customer_id": str(customer_id),
                    "total_amount": str(total_amount),
                },
                aggregate_type="Order",
                aggregate_id=order.id,
                correlation_id=correlation_id,
                causation_id=None,
                status=OutboxMessage.Status.PUBLISHED,
                published_at=created_at + timedelta(seconds=5),
                created_at=created_at,
            )

            if order.status == Order.Status.CONFIRMED:
                OutboxMessage.objects.create(
                    id=uuid.uuid4(),
                    message_type="OrderConfirmed",
                    payload={"order_id": str(order.id)},
                    aggregate_type="Order",
                    aggregate_id=order.id,
                    correlation_id=correlation_id,
                    causation_id=None,
                    status=OutboxMessage.Status.PUBLISHED,
                    published_at=updated_at + timedelta(seconds=5),
                    created_at=updated_at,
                )

            print(
                f"Created order {i + 1}/{total_orders}: {order.id} "
                f"(Status: {order.status}, Total: ${total_amount:.2f}, Date: {created_at.date()})"
            )

        # Create dead letters for DLQ
        dead_letter_count = 15
        for i in range(dead_letter_count):
            days_ago = random.randint(0, 30)
            created_at = now - timedelta(days=days_ago)

            correlation_id = uuid.uuid4()
            failure_type = random.choice(["payment_timeout", "stock_error", "gateway_error"])

            if failure_type == "payment_timeout":
                DeadLetterMessage.objects.create(
                    id=uuid.uuid4(),
                    queue_name="payments",
                    message_type="PaymentFailed",
                    payload={
                        "order_id": str(uuid.uuid4()),
                        "amount": str(random.uniform(50, 500)),
                    },
                    error_message="Payment gateway timeout after 30s",
                    retry_count=random.randint(1, 3),
                    correlation_id=correlation_id,
                    status=DeadLetterMessage.Status.PENDING,
                    created_at=created_at,
                )
            elif failure_type == "stock_error":
                DeadLetterMessage.objects.create(
                    id=uuid.uuid4(),
                    queue_name="inventory",
                    message_type="StockReservationFailed",
                    payload={
                        "order_id": str(uuid.uuid4()),
                        "product_id": str(uuid.uuid4()),
                    },
                    error_message="Insufficient stock for product",
                    retry_count=random.randint(1, 2),
                    correlation_id=correlation_id,
                    status=DeadLetterMessage.Status.PENDING,
                    created_at=created_at,
                )
            else:
                DeadLetterMessage.objects.create(
                    id=uuid.uuid4(),
                    queue_name="orchestrator",
                    message_type="SagaStepFailed",
                    payload={
                        "order_id": str(uuid.uuid4()),
                        "step": "PaymentProcessing",
                    },
                    error_message="Gateway connection refused",
                    retry_count=random.randint(2, 5),
                    correlation_id=correlation_id,
                    status=DeadLetterMessage.Status.PENDING,
                    created_at=created_at,
                )

            print(f"Created dead letter {i + 1}/{dead_letter_count} ({failure_type})")

        # Calculate and display statistics
        total_orders_count = Order.objects.count()
        confirmed_count = Order.objects.filter(status=Order.Status.CONFIRMED).count()
        cancelled_count = Order.objects.filter(status=Order.Status.CANCELLED).count()
        total_revenue = sum(
            order.total_amount for order in Order.objects.filter(status=Order.Status.CONFIRMED)
        )

        print("\n" + "=" * 60)
        print("DEMO DATA SEEDING COMPLETE")
        print("=" * 60)
        print(f"Products: {len(products)}")
        print(f"Total Orders: {total_orders_count}")
        print(f"Confirmed Orders: {confirmed_count}")
        print(f"Cancelled Orders: {cancelled_count}")
        print(f"Total Revenue: ${total_revenue:.2f}")
        print(f"Dead Letters: {dead_letter_count}")
        print(f"Date Range: {three_months_ago.date()} to {now.date()}")
        print("=" * 60)
