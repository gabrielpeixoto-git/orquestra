"""Tests for inventory services."""

import uuid
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.inventory.models import Product, StockReservation
from apps.inventory.services import (
    InsufficientStockError,
    ProductNotFoundError,
    ReservationNotFoundError,
    confirm_reservation,
    create_product,
    get_product,
    release_stock,
    reserve_stock,
)


class ReserveStockTests(TestCase):
    """Tests for reserve_stock service."""

    def test_reserve_stock_sufficient_quantity(self) -> None:
        """Test reserving stock when sufficient quantity is available."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        order_id = uuid.uuid4()

        reservation = reserve_stock(order_id, product.id, 10)

        assert reservation.order_id == order_id
        assert reservation.product_id == product.id
        assert reservation.quantity == 10
        assert reservation.status == StockReservation.Status.ACTIVE

        product.refresh_from_db()
        assert product.stock_quantity == 90

    def test_reserve_stock_insufficient_quantity_raises_error(self) -> None:
        """Test reserving stock with insufficient quantity raises error."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=5,
        )
        order_id = uuid.uuid4()

        with pytest.raises(InsufficientStockError):
            reserve_stock(order_id, product.id, 10)

    def test_reserve_stock_nonexistent_product_raises_error(self) -> None:
        """Test reserving stock for non-existent product raises error."""
        product_id = uuid.uuid4()
        order_id = uuid.uuid4()

        with pytest.raises(ProductNotFoundError):
            reserve_stock(order_id, product_id, 10)


class ReleaseStockTests(TestCase):
    """Tests for release_stock service."""

    def test_release_stock_reservation(self) -> None:
        """Test releasing a stock reservation."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        order_id = uuid.uuid4()
        reservation = reserve_stock(order_id, product.id, 10)

        released_reservation = release_stock(reservation.id)

        assert released_reservation.status == StockReservation.Status.RELEASED

        product.refresh_from_db()
        assert product.stock_quantity == 100

    def test_release_already_released_reservation(self) -> None:
        """Test releasing an already released reservation is idempotent."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        order_id = uuid.uuid4()
        reservation = reserve_stock(order_id, product.id, 10)
        release_stock(reservation.id)

        released_reservation = release_stock(reservation.id)

        assert released_reservation.status == StockReservation.Status.RELEASED

    def test_release_nonexistent_reservation_raises_error(self) -> None:
        """Test releasing a non-existent reservation raises error."""
        reservation_id = uuid.uuid4()

        with pytest.raises(ReservationNotFoundError):
            release_stock(reservation_id)


class ConfirmReservationTests(TestCase):
    """Tests for confirm_reservation service."""

    def test_confirm_reservation(self) -> None:
        """Test confirming a stock reservation."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        order_id = uuid.uuid4()
        reservation = reserve_stock(order_id, product.id, 10)

        confirmed_reservation = confirm_reservation(reservation.id)

        assert confirmed_reservation.status == StockReservation.Status.CONFIRMED

    def test_confirm_already_confirmed_reservation(self) -> None:
        """Test confirming an already confirmed reservation is idempotent."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        order_id = uuid.uuid4()
        reservation = reserve_stock(order_id, product.id, 10)
        confirm_reservation(reservation.id)

        confirmed_reservation = confirm_reservation(reservation.id)

        assert confirmed_reservation.status == StockReservation.Status.CONFIRMED

    def test_confirm_nonexistent_reservation_raises_error(self) -> None:
        """Test confirming a non-existent reservation raises error."""
        reservation_id = uuid.uuid4()

        with pytest.raises(ReservationNotFoundError):
            confirm_reservation(reservation_id)


class CreateProductTests(TestCase):
    """Tests for create_product service."""

    def test_create_product(self) -> None:
        """Test creating a new product."""
        product = create_product(
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

        assert product.name == "Test Product"
        assert product.description == "Test description"
        assert product.price == Decimal("10.00")
        assert product.stock_quantity == 100


class GetProductTests(TestCase):
    """Tests for get_product service."""

    def test_get_existing_product(self) -> None:
        """Test getting an existing product."""
        product_id = uuid.uuid4()
        Product.objects.create(
            id=product_id,
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

        product = get_product(product_id)

        assert product.id == product_id

    def test_get_nonexistent_product_raises_error(self) -> None:
        """Test getting a non-existent product raises error."""
        product_id = uuid.uuid4()

        with pytest.raises(ProductNotFoundError):
            get_product(product_id)
