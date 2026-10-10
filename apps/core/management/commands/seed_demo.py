"""Management command to seed demo data."""

import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Seed demo data for testing."""

    help = "Seed demo data for the application"

    def handle(self, *args, **options) -> None:
        """Execute the seed command."""
        from apps.inventory.models import Product
        from apps.orders.models import Order, OrderItem

        print("Seeding demo data...")

        # Clear existing data
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()

        # Create products
        products_data = [
            {
                "name": "Product A",
                "description": "High quality product A",
                "price": Decimal("100.00"),
                "stock_quantity": 50,
            },
            {
                "name": "Product B",
                "description": "Premium product B",
                "price": Decimal("250.00"),
                "stock_quantity": 30,
            },
            {
                "name": "Product C",
                "description": "Budget product C",
                "price": Decimal("50.00"),
                "stock_quantity": 100,
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

        # Create orders
        orders_data = [
            {
                "customer_id": uuid.uuid4(),
                "items": [
                    {
                        "product_id": products[0].id,
                        "quantity": 2,
                        "unit_price": products[0].price,
                    }
                ],
            },
            {
                "customer_id": uuid.uuid4(),
                "items": [
                    {
                        "product_id": products[1].id,
                        "quantity": 1,
                        "unit_price": products[1].price,
                    },
                    {
                        "product_id": products[2].id,
                        "quantity": 3,
                        "unit_price": products[2].price,
                    },
                ],
            },
        ]

        for order_data in orders_data:
            order = Order.objects.create(
                id=uuid.uuid4(),
                customer_id=order_data["customer_id"],
                total_amount=Decimal("0.00"),
                status=Order.Status.PENDING,
            )

            total_amount = Decimal("0.00")
            for item_data in order_data["items"]:
                total_price = item_data["unit_price"] * item_data["quantity"]
                total_amount += total_price

                OrderItem.objects.create(
                    id=uuid.uuid4(),
                    order=order,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                    total_price=total_price,
                )

            order.total_amount = total_amount
            order.save()

            print(
                f"Created order: {order.id} (Customer: {order.customer_id}, Total: {order.total_amount})"
            )

        print("Demo data seeded successfully!")
