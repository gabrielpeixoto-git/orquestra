from django.db import models


class AuditLog(models.Model):
    """Audit log for tracking important events."""

    class Action(models.TextChoices):
        ORDER_CREATED = "ORDER_CREATED", "Order Created"
        ORDER_CANCELLED = "ORDER_CANCELLED", "Order Cancelled"
        STOCK_RESERVED = "STOCK_RESERVED", "Stock Reserved"
        STOCK_RELEASED = "STOCK_RELEASED", "Stock Released"
        PAYMENT_PROCESSED = "PAYMENT_PROCESSED", "Payment Processed"
        PAYMENT_FAILED = "PAYMENT_FAILED", "Payment Failed"

    id = models.UUIDField(primary_key=True)
    action = models.CharField(max_length=50, choices=Action.choices)
    actor = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self) -> str:
        return f"AuditLog {self.id} - {self.action} on {self.entity_type}:{self.entity_id}"
