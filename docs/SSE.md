# SSE Integration Guide

## Overview

Server-Sent Events (SSE) are implemented for real-time updates, replacing polling-based HTMX refresh.

## Backend Implementation

### SSE Endpoint

- **URL**: `/sse/orders/`
- **Method**: GET
- **Headers**: `X-Client-Id: <unique-id>` (optional, auto-generated if not provided)

### Event Types

- `order_created`: New order created
- `order_updated`: Order status changed
- `dead_letter_added`: New dead letter
- `dead_letter_removed`: Dead letter replayed/discarded

### Example JavaScript Client

```javascript
const eventSource = new EventSource('/sse/orders/');
const clientId = crypto.randomUUID();
eventSource.setRequestHeader('X-Client-Id', clientId);

eventSource.addEventListener('order_created', (event) => {
  const data = JSON.parse(event.data);
  console.log('New order:', data);
  // Update UI
});

eventSource.addEventListener('order_updated', (event) => {
  const data = JSON.parse(event.data);
  console.log('Order updated:', data);
  // Update UI
});

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

## Broadcasting Events

```python
from apps.dashboard.sse_views import SSEClient

# Broadcast event to all connected clients
SSEClient.broadcast('order_created', {
  'order_id': str(order.id),
  'status': order.status,
  'total_amount': str(order.total_amount),
})
```

## Frontend Integration (HTMX Alternative)

The current implementation uses HTMX polling. To use SSE instead:

1. Remove `hx-trigger="every 5s"` from templates
2. Add SSE JavaScript client
3. Update UI on event reception

## Production Considerations

- SSE connections are stateful
- Load balancers must support long-lived connections
- Use Redis Pub/Sub for multi-instance deployments
- Add authentication for SSE endpoint
