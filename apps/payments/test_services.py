"""Tests for payment services."""

import uuid
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.payments.models import Payment
from apps.payments.services import (
    InvalidAmountError,
    PaymentDeclinedError,
    PaymentGatewayError,
    PaymentNotFoundError,
    PaymentTimeoutError,
    get_payment,
    get_payment_by_order,
    process_payment,
    refund_payment,
)


class ProcessPaymentTests(TestCase):
    """Tests for process_payment service."""

    def test_process_payment_success(self) -> None:
        """Test processing a successful payment."""
        order_id = uuid.uuid4()
        amount = Decimal("100.00")

        payment = process_payment(order_id, amount)

        assert payment.order_id == order_id
        assert payment.amount == amount
        assert payment.status == Payment.Status.SUCCEEDED


class PaymentModelTests(TestCase):
    """Tests for Payment model."""

    def test_payment_str_representation(self) -> None:
        """Test string representation of Payment."""
        from decimal import Decimal

        payment = Payment.objects.create(
            id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            gateway_transaction_id="txn_123",
        )

        str_repr = str(payment)
        assert "Payment" in str_repr
        assert str(payment.id) in str_repr
        assert "SUCCEEDED" in str_repr
        assert payment.gateway_transaction_id.startswith("txn_")

    def test_process_payment_with_large_amount_declined(self) -> None:
        """Test that payment with amount > 10000 is declined."""
        order_id = uuid.uuid4()
        amount = Decimal("15000.00")

        with pytest.raises(PaymentDeclinedError):
            process_payment(order_id, amount)

    def test_process_payment_with_zero_amount_raises_error(self) -> None:
        """Test that payment with zero amount raises error."""
        order_id = uuid.uuid4()
        amount = Decimal("0.00")

        with pytest.raises(InvalidAmountError):
            process_payment(order_id, amount)

    def test_process_payment_with_negative_amount_raises_error(self) -> None:
        """Test that payment with negative amount raises error."""
        order_id = uuid.uuid4()
        amount = Decimal("-10.00")

        with pytest.raises(InvalidAmountError):
            process_payment(order_id, amount)

    def test_process_payment_with_timeout_raises_error(self) -> None:
        """Test that payment with timeout raises error."""
        order_id = uuid.uuid4()
        amount = Decimal("100.00")

        with pytest.raises(PaymentTimeoutError):
            process_payment(order_id, amount, force_timeout=True)

    def test_process_payment_with_gateway_error_raises_error(self) -> None:
        """Test that payment with gateway error raises error."""
        order_id = uuid.uuid4()
        amount = Decimal("100.00")

        with pytest.raises(PaymentGatewayError):
            process_payment(order_id, amount, force_error=True)


class RefundPaymentTests(TestCase):
    """Tests for refund_payment service."""

    def test_refund_succeeded_payment(self) -> None:
        """Test refunding a succeeded payment."""
        payment = Payment.objects.create(
            id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            gateway_transaction_id="txn_123",
        )

        refunded_payment = refund_payment(payment.id)

        assert refunded_payment.status == Payment.Status.REFUNDED

    def test_refund_already_refunded_payment(self) -> None:
        """Test refunding an already refunded payment is idempotent."""
        payment = Payment.objects.create(
            id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            status=Payment.Status.REFUNDED,
            gateway_transaction_id="txn_123",
        )

        refunded_payment = refund_payment(payment.id)

        assert refunded_payment.status == Payment.Status.REFUNDED

    def test_refund_failed_payment_raises_error(self) -> None:
        """Test refunding a failed payment raises error."""
        payment = Payment.objects.create(
            id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            status=Payment.Status.FAILED,
            gateway_transaction_id="declined_123",
        )

        with pytest.raises(InvalidAmountError):
            refund_payment(payment.id)

    def test_refund_nonexistent_payment_raises_error(self) -> None:
        """Test refunding a non-existent payment raises error."""
        payment_id = uuid.uuid4()

        with pytest.raises(PaymentNotFoundError):
            refund_payment(payment_id)


class GetPaymentTests(TestCase):
    """Tests for get_payment service."""

    def test_get_existing_payment(self) -> None:
        """Test getting an existing payment."""
        payment_id = uuid.uuid4()
        Payment.objects.create(
            id=payment_id,
            order_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            gateway_transaction_id="txn_123",
        )

        payment = get_payment(payment_id)

        assert payment.id == payment_id

    def test_get_nonexistent_payment_raises_error(self) -> None:
        """Test getting a non-existent payment raises error."""
        payment_id = uuid.uuid4()

        with pytest.raises(PaymentNotFoundError):
            get_payment(payment_id)


class GetPaymentByOrderTests(TestCase):
    """Tests for get_payment_by_order service."""

    def test_get_payment_by_existing_order(self) -> None:
        """Test getting payment by existing order."""
        order_id = uuid.uuid4()
        Payment.objects.create(
            id=uuid.uuid4(),
            order_id=order_id,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            gateway_transaction_id="txn_123",
        )

        payment = get_payment_by_order(order_id)

        assert payment.order_id == order_id

    def test_get_payment_by_nonexistent_order_raises_error(self) -> None:
        """Test getting payment by non-existent order raises error."""
        order_id = uuid.uuid4()

        with pytest.raises(PaymentNotFoundError):
            get_payment_by_order(order_id)
