"""Views for outbox and dead letter message management."""

import structlog
from django.core.management import call_command
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.outbox.models import DeadLetterMessage, OutboxMessage
from apps.outbox.serializers import (
    DeadLetterMessageSerializer,
    OutboxMessageSerializer,
    ReplayDeadLetterSerializer,
)

logger = structlog.get_logger(__name__)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_outbox_messages(_request) -> Response:
    """List all outbox messages (staff only)."""
    messages = OutboxMessage.objects.all().order_by("-created_at")[:100]
    serializer = OutboxMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_dead_letters(request) -> Response:
    """List all dead letter messages (staff only)."""
    queue_name = request.query_params.get("queue")
    queryset = DeadLetterMessage.objects.filter(status=DeadLetterMessage.Status.PENDING)
    if queue_name:
        queryset = queryset.filter(queue_name=queue_name)
    messages = queryset.order_by("-created_at")[:100]
    serializer = DeadLetterMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def replay_dead_letter(request) -> Response:
    """Replay a dead letter message (staff only)."""
    serializer = ReplayDeadLetterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    dead_letter_id = serializer.validated_data["dead_letter_id"]

    try:
        dead_letter = DeadLetterMessage.objects.get(id=dead_letter_id)
    except DeadLetterMessage.DoesNotExist:
        return Response(
            {"error": "Dead letter message not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if dead_letter.status != DeadLetterMessage.Status.PENDING:
        return Response(
            {"error": "Message is not in pending status"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Replay the message
        call_command("replay_dlq", queue=dead_letter.queue_name, limit=1)
        return Response({"message": "Message replayed successfully"})
    except Exception as e:
        logger.exception("Failed to replay dead letter message", dead_letter_id=str(dead_letter_id))
        return Response(
            {"error": f"Failed to replay message: {e!s}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def discard_dead_letter(request) -> Response:
    """Discard a dead letter message (staff only)."""
    serializer = ReplayDeadLetterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    dead_letter_id = serializer.validated_data["dead_letter_id"]

    try:
        dead_letter = DeadLetterMessage.objects.get(id=dead_letter_id)
    except DeadLetterMessage.DoesNotExist:
        return Response(
            {"error": "Dead letter message not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if dead_letter.status != DeadLetterMessage.Status.PENDING:
        return Response(
            {"error": "Message is not in pending status"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from apps.outbox.services_deadletter import mark_dead_letter_discarded

    mark_dead_letter_discarded(dead_letter_id)
    return Response({"message": "Message discarded successfully"})
