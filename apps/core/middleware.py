"""Middleware for Orquestra."""

import uuid

import structlog
from django.utils.deprecation import MiddlewareMixin


class CorrelationIdMiddleware(MiddlewareMixin):
    """Middleware to add correlation ID to requests."""

    def process_request(self, request):
        """Add correlation ID to request context.

        Args:
            request: HTTP request object.
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.correlation_id = correlation_id

        # Add to structlog context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    def process_response(self, request, response):
        """Add correlation ID to response headers.

        Args:
            request: HTTP request object.
            response: HTTP response object.

        Returns:
            HTTP response object with correlation ID header.
        """
        correlation_id = getattr(request, "correlation_id", None)
        if correlation_id:
            response["X-Correlation-ID"] = correlation_id

        # Clear context for next request
        structlog.contextvars.clear_contextvars()

        return response
