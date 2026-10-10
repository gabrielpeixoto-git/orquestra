"""Tests for idempotency of operations."""

import uuid
from decimal import Decimal

from django.test import TestCase

from apps.inventory.models import Product
from apps.inventory.services import confirm_reservation, release_stock, reserve_stock
from apps.orders.models import Order
from apps.orders.services import cancel_order
from apps.payments.models import Payment
from apps.payments.services import refund_payment


class IdempotencyTests(TestCase):
    """Tests for idempotency of operations."""

    def test_cancel_order_idempotent(self) -> None:
        """Test that cancelling an already cancelled order is idempotent."""
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            total_amount=Decimal("100.00"),
            status=Order.Status.PENDING,
        )

        first_cancel = cancel_order(order.id)
        second_cancel = cancel_order(order.id)

        assert first_cancel.status == Order.Status.CANCELLED
        assert second_cancel.status == Order.Status.CANCELLED
        assert first_cancel.id == second_cancel.id

    def test_release_stock_idempotent(self) -> None:
        """Test that releasing an already released reservation is idempotent."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        order_id = uuid.uuid4()
        reservation = reserve_stock(order_id, product.id, 10)

        first_release = release_stock(reservation.id)
        second_release = release_stock(reservation.id)

        assert first_release.status == "RELEASED"
        assert second_release.status == "RELEASED"
        assert first_release.id == second_release.id

        product.refresh_from_db()
        assert product.stock_quantity == 100

    def test_confirm_reservation_idempotent(self) -> None:
        """Test that confirming an already confirmed reservation is idempotent."""
        product = Product.objects.create(
            id=uuid.uuid4(),
            name="Test Product",
            description="Test description",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        order_id = uuid.uuid4()
        reservation = reserve_stock(order_id, product.id, 10)

        first_confirm = confirm_reservation(reservation.id)
        second_confirm = confirm_reservation(reservation.id)

        assert first_confirm.status == "CONFIRMED"
        assert second_confirm.status == "CONFIRMED"
        assert first_confirm.id == second_confirm.id

    def test_refund_payment_idempotent(self) -> None:
        """Test that refunding an already refunded payment is idempotent."""
        payment = Payment.objects.create(
            id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            gateway_transaction_id="txn_123",
        )

        first_refund = refund_payment(payment.id)
        second_refund = refund_payment(payment.id)

        assert first_refund.status == Payment.Status.REFUNDED
        assert second_refund.status == Payment.Status.REFUNDED
        assert first_refund.id == second_refund.id

    def test_idempotent_operations_do_not_accumulate_effects(self) -> None:
        """Test that repeated idempotent operations do not accumulate effects."""
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
        release_stock(reservation.id)
        release_stock(reservation.id)

        product.refresh_from_db()
        assert product.stock_quantity == 100
