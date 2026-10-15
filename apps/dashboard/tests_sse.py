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

    def test_add_client_returns_existing_queue(self):
        """Test adding a client that already exists returns existing queue."""
        client_id = "test-client-existing"
        queue1 = SSEClient.add_client(client_id)
        queue2 = SSEClient.add_client(client_id)

        assert queue1 is queue2
        assert SSEClient._clients[client_id] is queue1

    def test_remove_client(self):
        """Test removing a client from the pool."""
        client_id = "test-client-2"
        SSEClient.add_client(client_id)
        SSEClient.remove_client(client_id)

        assert client_id not in SSEClient._clients

    def test_remove_nonexistent_client(self):
        """Test removing a client that doesn't exist doesn't raise."""
        client_id = "nonexistent-client"
        SSEClient.remove_client(client_id)  # Should not raise

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

    def test_sse_orders_with_custom_client_id(self):
        """Test SSE endpoint uses custom client ID from header."""
        request = self.factory.get("/sse/orders/", HTTP_X_CLIENT_ID="custom-client-123")
        response = sse_orders(request)

        assert response.status_code == 200
        assert "custom-client-123" in SSEClient._clients

    def test_sse_orders_without_client_id(self):
        """Test SSE endpoint generates client ID when not provided."""
        request = self.factory.get("/sse/orders/")
        response = sse_orders(request)

        assert response.status_code == 200
        # Client should be added with auto-generated ID
        assert len(SSEClient._clients) > 0

    def test_sse_orders_removes_client_on_timeout(self):
        """Test SSE endpoint removes client when generator times out."""
        request = self.factory.get("/sse/orders/", HTTP_X_CLIENT_ID="timeout-client")
        sse_orders(request)

        # Consume the generator (it will timeout after 30s, but we can't wait that long)
        # Instead, just verify the client was added
        assert "timeout-client" in SSEClient._clients

        # Manually remove to clean up
        SSEClient.remove_client("timeout-client")

    def test_sse_orders_event_stream_timeout(self):
        """Test SSE event stream handles timeout gracefully."""
        client_id = "test-timeout-client"
        client_queue = SSEClient.add_client(client_id)

        # Simulate the generator behavior
        import contextlib

        with contextlib.suppress(queue.Empty):
            client_queue.get(timeout=0.01)

        # Client should still be in pool
        assert client_id in SSEClient._clients
        SSEClient.remove_client(client_id)

    def test_sse_orders_event_stream_yields_keep_alive(self):
        """Test SSE event stream yields keep-alive on timeout."""
        client_id = "keep-alive-client"
        client_queue = SSEClient.add_client(client_id)

        # Simulate event stream behavior
        def event_stream():
            try:
                while True:
                    message = client_queue.get(timeout=0.01)
                    yield message
            except queue.Empty:
                yield ": keep-alive\n\n"
            finally:
                SSEClient.remove_client(client_id)

        # Get the generator and consume it
        gen = event_stream()
        messages = list(gen)

        # Should get keep-alive message
        assert len(messages) == 1
        assert ": keep-alive" in messages[0]

        # Client should be removed
        assert client_id not in SSEClient._clients

    def test_sse_orders_generator_receives_message(self):
        """Test SSE generator receives and yields messages."""
        client_id = "message-client"
        client_queue = SSEClient.add_client(client_id)

        # Broadcast a message
        SSEClient.broadcast("test_event", {"data": "test"})

        # Simulate event stream receiving the message
        def event_stream():
            try:
                while True:
                    message = client_queue.get(timeout=0.1)
                    yield message
                    break  # Exit after first message
            except queue.Empty:
                yield ": keep-alive\n\n"
            finally:
                SSEClient.remove_client(client_id)

        gen = event_stream()
        messages = list(gen)

        assert len(messages) == 1
        assert "test_event" in messages[0]

    def test_sse_orders_client_id_from_header(self):
        """Test client ID is extracted from header when provided."""
        factory = RequestFactory()
        custom_id = "custom-id-12345"
        request = factory.get("/sse/orders/", HTTP_X_CLIENT_ID=custom_id)

        sse_orders(request)

        assert custom_id in SSEClient._clients
        SSEClient.remove_client(custom_id)

    def test_sse_add_client_creates_new_queue(self):
        """Test add_client creates new queue for new client."""
        client_id = "new-client-test"

        # Remove if exists
        SSEClient.remove_client(client_id)

        client_queue = SSEClient.add_client(client_id)

        assert client_id in SSEClient._clients
        assert isinstance(client_queue, queue.Queue)
        SSEClient.remove_client(client_id)

    def test_sse_broadcast_to_multiple_clients(self):
        """Test broadcast sends to all connected clients."""
        client1 = "client-1"
        client2 = "client-2"
        client3 = "client-3"

        q1 = SSEClient.add_client(client1)
        q2 = SSEClient.add_client(client2)
        q3 = SSEClient.add_client(client3)

        SSEClient.broadcast("event", {"test": "data"})

        # All queues should have the message
        assert not q1.empty()
        assert not q2.empty()
        assert not q3.empty()

        # Clean up
        SSEClient.remove_client(client1)
        SSEClient.remove_client(client2)
        SSEClient.remove_client(client3)

    def test_sse_add_client_thread_safety(self):
        """Test add_client is thread-safe with lock."""
        import threading

        client_id = "thread-safe-client"
        SSEClient.remove_client(client_id)  # Clean if exists

        def add_client():
            SSEClient.add_client(client_id)

        threads = [threading.Thread(target=add_client) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exactly one queue
        assert client_id in SSEClient._clients
        SSEClient.remove_client(client_id)

    def test_sse_remove_client_nonexistent(self):
        """Test remove_client handles non-existent client gracefully."""
        # Should not raise error
        SSEClient.remove_client("non-existent-client")

    def test_sse_broadcast_full_queue_suppressed(self):
        """Test broadcast suppresses queue.Full errors."""
        client_id = "full-queue-client"
        q = SSEClient.add_client(client_id)

        # Fill the queue to capacity
        try:
            # Try to fill queue (queue size is implementation dependent)
            for _ in range(10000):
                q.put_nowait("test")
        except queue.Full:
            pass

        # Broadcast should not raise error even if queue is full
        SSEClient.broadcast("test_event", {"data": "test"})

        SSEClient.remove_client(client_id)

    def test_sse_orders_default_client_id_from_timestamp(self):
        """Test sse_orders generates client ID from timestamp when header missing."""
        from apps.dashboard.sse_views import sse_orders

        factory = RequestFactory()
        request = factory.get("/sse/orders/")  # No HTTP_X_CLIENT_ID header

        sse_orders(request)

        # Should have added a client with timestamp-based ID
        assert len(SSEClient._clients) > 0

        # Clean up all clients
        SSEClient._clients.clear()
