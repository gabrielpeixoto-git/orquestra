"""Views for orders API."""

import uuid

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.serializers import CreateOrderSerializer, OrderDetailSerializer
from apps.orders.services import OrderCreationError, OrderNotFoundError, create_order, get_order

logger = structlog.get_logger(__name__)


class CreateOrderView(APIView):
    """API view for creating orders."""

    def post(self, request) -> Response:
        """Create a new order.

        Request body:
        {
            "customer_id": "uuid",
            "items": [
                {
                    "product_id": "uuid",
                    "quantity": 2,
                    "unit_price": 100.00
                }
            ]
        }
        """
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer_id = serializer.validated_data["customer_id"]
        items = serializer.validated_data["items"]

        try:
            order = create_order(customer_id=customer_id, items=items)
            response_serializer = OrderDetailSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except OrderCreationError as e:
            logger.exception("Failed to create order")
            return Response(
                {"error": "Failed to create order", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OrderDetailView(APIView):
    """API view for retrieving order details."""

    def get(self, _request: object, order_id: uuid.UUID) -> Response:
        """Get order details by ID.

        Args:
            order_id: UUID of the order.
        """
        try:
            order = get_order(order_id=order_id)
            serializer = OrderDetailSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except OrderNotFoundError as e:
            logger.exception("Order not found", order_id=str(order_id))
            return Response(
                {"error": "Order not found", "detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
