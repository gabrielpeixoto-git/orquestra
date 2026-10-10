"""Serializers for orders API."""

from decimal import Decimal

from rest_framework import serializers

from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.Serializer):
    """Serializer for order items."""

    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )


class OrderItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for order item details."""

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "quantity", "unit_price", "total_price"]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""

    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_id",
            "total_amount",
            "status",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "total_amount", "status", "created_at", "updated_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order details with items."""

    items = OrderItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_id",
            "total_amount",
            "status",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_id",
            "total_amount",
            "status",
            "created_at",
            "updated_at",
        ]


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating orders."""

    customer_id = serializers.UUIDField()
    items = OrderItemSerializer(many=True)

    def validate_items(self, value: list[dict]) -> list[dict]:
        """Validate that items list is not empty."""
        if not value:
            error_msg = "At least one item is required."
            raise serializers.ValidationError(error_msg)
        return value
