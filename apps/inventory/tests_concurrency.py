"""Tests for stock reservation concurrency (prevent overselling)."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.inventory.models import Product
from apps.inventory.services import InsufficientStockError, reserve_stock


class StockConcurrencyTests(TestCase):
    """Tests for concurrent stock reservation to prevent overselling."""

    def test_concurrent_reservations_prevent_overselling(self) -> None:
        """Test that concurrent reservations respect stock limits."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=10,
        )

        successful_reservations = []
        failed_reservations = []

        def reserve_item(order_id: uuid.UUID) -> None:
            """Reserve stock for a single item."""
            try:
                reservation = reserve_stock(order_id, product.id, 1)
                successful_reservations.append(reservation.id)
            except InsufficientStockError:
                failed_reservations.append(order_id)

        order_ids = [uuid.uuid4() for _ in range(15)]

        with ThreadPoolExecutor(max_workers=15) as executor:
            executor.map(reserve_item, order_ids)

        product.refresh_from_db()

        assert len(successful_reservations) == 10
        assert len(failed_reservations) == 5
        assert product.stock_quantity == 0

    def test_concurrent_reservations_with_select_for_update(self) -> None:
        """Test that select_for_update prevents race conditions."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=5,
        )

        successful_reservations = []

        def reserve_multiple_items(order_id: uuid.UUID) -> None:
            """Reserve 2 items for each order."""
            try:
                reservation = reserve_stock(order_id, product.id, 2)
                successful_reservations.append(reservation.id)
            except InsufficientStockError:
                pass

        order_ids = [uuid.uuid4() for _ in range(5)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(reserve_multiple_items, order_ids)

        product.refresh_from_db()

        assert len(successful_reservations) == 2
        assert product.stock_quantity == 1

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
