"""Tests for stock reservation operations."""

import uuid
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.inventory.models import Product
from apps.inventory.services import InsufficientStockError, reserve_stock


class StockOperationsTests(TestCase):
    """Tests for stock reservation operations."""

    def test_sequential_reservations_work_correctly(self) -> None:
        """Test that sequential reservations work correctly."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=10,
        )

        for _ in range(10):
            order_id = uuid.uuid4()
            reserve_stock(order_id, product.id, 1)

        product.refresh_from_db()

        assert product.stock_quantity == 0

        with pytest.raises(InsufficientStockError):
            reserve_stock(uuid.uuid4(), product.id, 1)

    def test_reserve_stock_creates_reservation(self) -> None:
        """Test that reserving stock creates a reservation record."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=10,
        )

        order_id = uuid.uuid4()
        reservation = reserve_stock(order_id, product.id, 5)

        assert reservation.order_id == order_id
        assert reservation.product_id == product.id
        assert reservation.quantity == 5

        product.refresh_from_db()
        assert product.stock_quantity == 5
