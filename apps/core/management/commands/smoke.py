"""Management command to run smoke tests for the saga flow."""

import uuid
from decimal import Decimal

import structlog
from django.core.management.base import BaseCommand

from apps.inventory.services import create_product
from apps.orders.services import create_order
from apps.outbox.models import OutboxMessage

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Run smoke tests for the saga flow."""

    help = "Run smoke tests for the complete saga flow"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--scenario",
            type=str,
            default="success",
            choices=[
                "success",
                "insufficient_stock",
                "payment_failed",
                "payment_timeout",
                "payment_error",
            ],
            help="Test scenario to run",
        )

    def handle(self, *args, **options) -> None:
        """Execute the smoke test."""
        scenario = options["scenario"]

        logger.info("Starting smoke test", scenario=scenario)

        if scenario == "success":
            self.test_success_scenario()
        elif scenario == "insufficient_stock":
            self.test_insufficient_stock_scenario()
        elif scenario == "payment_failed":
            self.test_payment_failed_scenario()
        elif scenario == "payment_timeout":
            self.test_payment_timeout_scenario()
        elif scenario == "payment_error":
            self.test_payment_error_scenario()

        logger.info("Smoke test completed", scenario=scenario)

    def test_success_scenario(self) -> None:
        """Test successful order flow."""
        self.stdout.write("Testing successful order flow...")

        # Create a product with sufficient stock
        product = create_product(
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

        # Create an order
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": product.id,
                "quantity": 2,
                "unit_price": "10.00",
            }
        ]

        order = create_order(customer_id, items)

        # Check that order was created
        assert order.status == "PENDING"
        assert order.total_amount == Decimal("20.00")

        # Check that outbox message was created
        outbox_messages = OutboxMessage.objects.filter(aggregate_id=order.id)
        assert outbox_messages.count() == 1
        assert outbox_messages.first().message_type == "OrderCreated"

        self.stdout.write(self.style.SUCCESS("[OK] Order created successfully"))
        self.stdout.write(self.style.SUCCESS("[OK] Outbox message created"))

        # Note: Full saga flow requires Celery workers and RabbitMQ to be running
        # This test validates the synchronous part of the flow
        self.stdout.write(
            self.style.WARNING("[WARN] Full saga flow requires Celery workers and RabbitMQ")
        )
        self.stdout.write(self.style.SUCCESS("[OK] Success scenario passed (synchronous part)"))

    def test_insufficient_stock_scenario(self) -> None:
        """Test order flow with insufficient stock."""
        self.stdout.write("Testing insufficient stock scenario...")

        # Create a product with limited stock
        product = create_product(
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=5,
        )

        # Create an order with more items than available
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": product.id,
                "quantity": 10,
                "unit_price": "10.00",
            }
        ]

        order = create_order(customer_id, items)

        # Check that order was created
        assert order.status == "PENDING"

        self.stdout.write(self.style.SUCCESS("[OK] Order created with insufficient stock"))
        self.stdout.write(
            self.style.WARNING("[WARN] Full flow requires Celery workers and RabbitMQ")
        )

    def test_payment_failed_scenario(self) -> None:
        """Test order flow with payment failure."""
        self.stdout.write("Testing payment failed scenario...")

        # Create a product
        product = create_product(
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

        # Create an order with large amount (will fail in payment gateway)
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": product.id,
                "quantity": 2,
                "unit_price": "6000.00",  # Amount > 10000, will fail
            }
        ]

        order = create_order(customer_id, items)

        # Check that order was created
        assert order.status == "PENDING"

        self.stdout.write(self.style.SUCCESS("[OK] Order created with large amount"))
        self.stdout.write(
            self.style.WARNING("[WARN] Full flow requires Celery workers and RabbitMQ")
        )

    def test_payment_timeout_scenario(self) -> None:
        """Test order flow with payment timeout."""
        self.stdout.write("Testing payment timeout scenario...")

        # Create a product
        product = create_product(
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

        # Create an order
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": product.id,
                "quantity": 2,
                "unit_price": "10.00",
            }
        ]

        create_order(customer_id, items)

        self.stdout.write(self.style.SUCCESS("[OK] Order created"))
        self.stdout.write(
            self.style.WARNING("[WARN] Payment timeout simulation requires manual testing")
        )

    def test_payment_error_scenario(self) -> None:
        """Test order flow with payment gateway error."""
        self.stdout.write("Testing payment gateway error scenario...")

        # Create a product
        product = create_product(
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

        # Create an order
        customer_id = uuid.uuid4()
        items = [
            {
                "product_id": product.id,
                "quantity": 2,
                "unit_price": "10.00",
            }
        ]

        create_order(customer_id, items)

        self.stdout.write(self.style.SUCCESS("[OK] Order created"))
        self.stdout.write(
            self.style.WARNING("[WARN] Payment error simulation requires manual testing")
        )
