import uuid

from django.db import models


class OutboxMessage(models.Model):
    """Transactional outbox message for reliable event publishing."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PUBLISHED = "PUBLISHED", "Published"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    message_type = models.CharField(max_length=255)
    payload = models.JSONField()
    aggregate_type = models.CharField(max_length=50)
    aggregate_id = models.UUIDField()
    correlation_id = models.UUIDField()
    causation_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "outbox_messages"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["aggregate_type", "aggregate_id"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self) -> str:
        return f"OutboxMessage {self.id} - {self.message_type} ({self.status})"


class DeadLetterMessage(models.Model):
    """Dead letter message for failed message handling."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REPLAYED = "REPLAYED", "Replayed"
        DISCARDED = "DISCARDED", "Discarded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    queue_name = models.CharField(max_length=255)
    message_type = models.CharField(max_length=255)
    payload = models.JSONField()
    error_message = models.TextField()
    retry_count = models.IntegerField(default=0)
    correlation_id = models.UUIDField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    replayed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dead_letter_messages"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["queue_name"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self) -> str:
        return f"DeadLetterMessage {self.id} - {self.queue_name} ({self.status})"
