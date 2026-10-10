import uuid

from django.db import models


class InboxMessage(models.Model):
    """Inbox message for idempotent message processing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    consumer = models.CharField(max_length=255)
    message_id = models.UUIDField()
    message_type = models.CharField(max_length=255)
    payload = models.JSONField()
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inbox_messages"
        unique_together = [["consumer", "message_id"]]
        indexes = [
            models.Index(fields=["consumer", "message_id"]),
            models.Index(fields=["processed_at"]),
        ]

    def __str__(self) -> str:
        return f"InboxMessage {self.id} - {self.consumer}:{self.message_id}"
