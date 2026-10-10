/* SSE client for real-time updates */

class SSEClient {
  constructor(url, eventHandlers = {}) {
    this.url = url;
    this.eventHandlers = eventHandlers;
    this.eventSource = null;
    this.clientId = this.generateClientId();
    this.reconnectDelay = 3000;
    this.maxReconnectAttempts = 10;
    this.reconnectAttempts = 0;
  }

  generateClientId() {
    return crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36);
  }

  connect() {
    try {
      this.eventSource = new EventSource(this.url);

      this.eventSource.addEventListener('order_created', (event) => {
        this.handleEvent('order_created', event);
      });

      this.eventSource.addEventListener('order_updated', (event) => {
        this.handleEvent('order_updated', event);
      });

      this.eventSource.addEventListener('dead_letter_added', (event) => {
        this.handleEvent('dead_letter_added', event);
      });

      this.eventSource.addEventListener('dead_letter_removed', (event) => {
        this.handleEvent('dead_letter_removed', event);
      });

      this.eventSource.addEventListener('health_update', (event) => {
        this.handleEvent('health_update', event);
      });

      this.eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        this.handleReconnect();
      };

      this.eventSource.onopen = () => {
        console.log('SSE connected');
        this.reconnectAttempts = 0;
      };
    } catch (error) {
      console.error('Failed to create EventSource:', error);
      this.handleReconnect();
    }
  }

  handleEvent(eventType, event) {
    try {
      const data = JSON.parse(event.data);
      if (this.eventHandlers[eventType]) {
        this.eventHandlers[eventType](data);
      }
    } catch (error) {
      console.error(`Failed to parse ${eventType} event:`, error);
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => {
        this.disconnect();
        this.connect();
      }, this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

/* Global SSE instance */
let sseClient = null;

function initSSE() {
  if (sseClient) {
    sseClient.disconnect();
  }

  sseClient = new SSEClient('/sse/orders/', {
    order_created: (data) => {
      console.log('Order created:', data);
      if (window.location.pathname === '/orders/') {
        // Refresh orders table
        htmx.ajax('GET', '/orders/', {target: '#orders-table-body', swap: 'innerHTML'});
      }
    },
    order_updated: (data) => {
      console.log('Order updated:', data);
      if (window.location.pathname === '/orders/') {
        // Refresh orders table
        htmx.ajax('GET', '/orders/', {target: '#orders-table-body', swap: 'innerHTML'});
      }
    },
    dead_letter_added: (data) => {
      console.log('Dead letter added:', data);
      if (window.location.pathname === '/dead-letters/') {
        // Refresh dead letters table
        htmx.ajax('GET', '/dead-letters/', {target: '#dead-letters-table-body', swap: 'innerHTML'});
      }
    },
    dead_letter_removed: (data) => {
      console.log('Dead letter removed:', data);
      if (window.location.pathname === '/dead-letters/') {
        // Refresh dead letters table
        htmx.ajax('GET', '/dead-letters/', {target: '#dead-letters-table-body', swap: 'innerHTML'});
      }
    },
    health_update: (data) => {
      console.log('Health update:', data);
      if (window.location.pathname === '/health/') {
        // Refresh health content
        htmx.ajax('GET', '/health/', {target: '#health-content', swap: 'innerHTML'});
      }
    },
  });

  sseClient.connect();
}

/* Initialize SSE on page load */
document.addEventListener('DOMContentLoaded', () => {
  initSSE();
});

/* Disconnect SSE on page unload */
window.addEventListener('beforeunload', () => {
  if (sseClient) {
    sseClient.disconnect();
  }
});
