from django.db import models


class Order(models.Model):
    """Order model representing a customer order."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        STOCK_RESERVED = "STOCK_RESERVED", "Stock Reserved"
        PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED", "Payment Succeeded"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True)
    customer_id = models.UUIDField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"

    def __str__(self) -> str:
        return f"Order {self.id} - {self.status}"


class OrderItem(models.Model):
    """Order item representing a product in an order."""

    id = models.UUIDField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "order_items"

    def __str__(self) -> str:
        return f"OrderItem {self.id} - {self.product_id} x{self.quantity}"
