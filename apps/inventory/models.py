from django.db import models


class Product(models.Model):
    """Product model representing inventory items."""

    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "products"

    def __str__(self) -> str:
        return f"{self.name} - ${self.price}"


class StockReservation(models.Model):
    """Stock reservation for orders."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CONFIRMED = "CONFIRMED", "Confirmed"
        RELEASED = "RELEASED", "Released"

    id = models.UUIDField(primary_key=True)
    order_id = models.UUIDField()
    product_id = models.UUIDField()
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "stock_reservations"
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["product_id"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self) -> str:
        return f"Reservation {self.id} - {self.product_id} x{self.quantity}"
