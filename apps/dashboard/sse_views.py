"""SSE views for real-time updates."""

import contextlib
import json
import queue
import threading
from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse
from django.utils import timezone


class SSEClient:
    """Manages SSE client connections."""

    _clients: dict[str, queue.Queue] = {}
    _lock = threading.Lock()

    @classmethod
    def add_client(cls, client_id: str) -> queue.Queue:
        """Add a new client to the pool.

        Args:
            client_id: Unique identifier for the client.

        Returns:
            Queue for the client.
        """
        with cls._lock:
            if client_id not in cls._clients:
                cls._clients[client_id] = queue.Queue()
            return cls._clients[client_id]

    @classmethod
    def remove_client(cls, client_id: str) -> None:
        """Remove a client from the pool.

        Args:
            client_id: Unique identifier for the client.
        """
        with cls._lock:
            cls._clients.pop(client_id, None)

    @classmethod
    def broadcast(cls, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all connected clients.

        Args:
            event_type: Type of event.
            data: Event data.
        """
        message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        with cls._lock:
            for client_queue in cls._clients.values():
                with contextlib.suppress(queue.Full):
                    client_queue.put_nowait(message)


@login_required
def sse_orders(request):
    """SSE endpoint for real-time order updates.

    Args:
        request: HTTP request.

    Returns:
        StreamingHttpResponse with SSE events.
    """
    client_id = request.META.get("HTTP_X_CLIENT_ID", str(timezone.now().timestamp()))
    client_queue = SSEClient.add_client(client_id)

    def event_stream():
        """Generator for SSE events."""
        try:
            while True:
                message = client_queue.get(timeout=30)
                yield message
        except queue.Empty:
            yield ": keep-alive\n\n"
        finally:
            SSEClient.remove_client(client_id)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
