"""Serializers for outbox and dead letter messages."""

from rest_framework import serializers

from apps.outbox.models import DeadLetterMessage, OutboxMessage


class OutboxMessageSerializer(serializers.ModelSerializer):
    """Serializer for OutboxMessage."""

    class Meta:
        model = OutboxMessage
        fields = [
            "id",
            "message_type",
            "payload",
            "aggregate_type",
            "aggregate_id",
            "correlation_id",
            "causation_id",
            "status",
            "published_at",
            "created_at",
        ]
        read_only_fields = fields


class DeadLetterMessageSerializer(serializers.ModelSerializer):
    """Serializer for DeadLetterMessage."""

    class Meta:
        model = DeadLetterMessage
        fields = [
            "id",
            "queue_name",
            "message_type",
            "payload",
            "error_message",
            "retry_count",
            "correlation_id",
            "status",
            "replayed_at",
            "created_at",
        ]
        read_only_fields = fields


class ReplayDeadLetterSerializer(serializers.Serializer):
    """Serializer for replay dead letter message request."""

    dead_letter_id = serializers.UUIDField()
