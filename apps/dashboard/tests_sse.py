"""Tests for SSE views."""

import json
import queue

from django.test import RequestFactory, TestCase

from apps.dashboard.sse_views import SSEClient, sse_orders


class SSEClientTests(TestCase):
    """Tests for SSEClient class."""

    def test_add_client(self):
        """Test adding a client to the pool."""
        client_id = "test-client-1"
        client_queue = SSEClient.add_client(client_id)

        assert isinstance(client_queue, queue.Queue)
        assert client_id in SSEClient._clients

    def test_remove_client(self):
        """Test removing a client from the pool."""
        client_id = "test-client-2"
        SSEClient.add_client(client_id)
        SSEClient.remove_client(client_id)

        assert client_id not in SSEClient._clients

    def test_broadcast(self):
        """Test broadcasting an event to all clients."""
        client_id_1 = "test-client-3"
        client_id_2 = "test-client-4"

        queue_1 = SSEClient.add_client(client_id_1)
        queue_2 = SSEClient.add_client(client_id_2)

        event_type = "order_created"
        data = {"order_id": "123", "status": "PENDING"}

        SSEClient.broadcast(event_type, data)

        assert not queue_1.empty()
        assert not queue_2.empty()

        message_1 = queue_1.get_nowait()
        message_2 = queue_2.get_nowait()

        assert event_type in message_1
        assert json.dumps(data) in message_1
        assert message_1 == message_2

    def test_broadcast_with_full_queue(self):
        """Test broadcasting handles full queues gracefully."""
        client_id = "test-client-5"
        client_queue = SSEClient.add_client(client_id)

        # Fill the queue to capacity
        max_size = 1000
        for _ in range(max_size):
            client_queue.put_nowait("test")

        # This should not raise an exception
        SSEClient.broadcast("test_event", {"test": "data"})


class SSEViewsTests(TestCase):
    """Tests for SSE views."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    def test_sse_orders_response_headers(self):
        """Test SSE endpoint returns correct headers."""
        request = self.factory.get("/sse/orders/")
        response = sse_orders(request)

        assert response["Content-Type"] == "text/event-stream"
        assert response["Cache-Control"] == "no-cache"
        assert response["X-Accel-Buffering"] == "no"

    def test_sse_orders_returns_streaming_response(self):
        """Test SSE endpoint returns StreamingHttpResponse."""
        request = self.factory.get("/sse/orders/")
        response = sse_orders(request)

        assert response.status_code == 200
        assert response.streaming
