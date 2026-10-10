"""Services for payment processing."""

import time
import uuid
from decimal import Decimal

import structlog

from apps.payments.models import Payment

logger = structlog.get_logger(__name__)


class PaymentDeclinedError(Exception):
    """Error raised when payment is declined by gateway."""


class PaymentNotFoundError(Exception):
    """Error raised when payment is not found."""


class InvalidAmountError(Exception):
    """Error raised when payment amount is invalid."""


class PaymentTimeoutError(Exception):
    """Error raised when payment gateway times out."""


class PaymentGatewayError(Exception):
    """Error raised when payment gateway has an internal error."""


def process_payment(
    order_id: uuid.UUID,
    amount: Decimal,
    force_timeout: bool = False,
    force_error: bool = False,
) -> Payment:
    """Process a payment using a fake gateway.

    Args:
        order_id: UUID of the order.
        amount: Payment amount.
        force_timeout: Force a timeout for testing (default: False).
        force_error: Force a gateway error for testing (default: False).

    Returns:
        The created Payment instance.

    Raises:
        InvalidAmountError: If amount is invalid.
        PaymentDeclinedError: If payment is declined by gateway.
        PaymentTimeoutError: If gateway times out.
        PaymentGatewayError: If gateway has an internal error.
    """
    logger.info(
        "Processing payment",
        order_id=str(order_id),
        amount=str(amount),
        force_timeout=force_timeout,
        force_error=force_error,
    )

    if amount <= 0:
        logger.error("Invalid payment amount", order_id=str(order_id), amount=str(amount))
        error_msg = f"Invalid payment amount: {amount}"
        raise InvalidAmountError(error_msg)

    # Simulate timeout for testing
    if force_timeout:
        logger.warning("Simulating gateway timeout", order_id=str(order_id))
        time.sleep(30)  # Simulate timeout
        error_msg = f"Payment gateway timeout for order {order_id}"
        raise PaymentTimeoutError(error_msg)

    # Simulate gateway error for testing
    if force_error:
        logger.warning("Simulating gateway error", order_id=str(order_id))
        error_msg = f"Payment gateway internal error for order {order_id}"
        raise PaymentGatewayError(error_msg)

    # Fake gateway logic - decline payments with amount > 10000
    if amount > Decimal("10000.00"):
        logger.warning("Payment declined by gateway", order_id=str(order_id), amount=str(amount))
        payment = Payment.objects.create(
            id=uuid.uuid4(),
            order_id=order_id,
            amount=amount,
            status=Payment.Status.FAILED,
            gateway_transaction_id=f"declined_{uuid.uuid4()}",
        )
        error_msg = f"Payment declined by gateway for order {order_id}"
        raise PaymentDeclinedError(error_msg)

    # Simulate successful payment
    payment = Payment.objects.create(
        id=uuid.uuid4(),
        order_id=order_id,
        amount=amount,
        status=Payment.Status.SUCCEEDED,
        gateway_transaction_id=f"txn_{uuid.uuid4()}",
    )

    logger.info(
        "Payment processed successfully",
        payment_id=str(payment.id),
        order_id=str(order_id),
        amount=str(amount),
    )
    return payment


def refund_payment(payment_id: uuid.UUID) -> Payment:
    """Refund a payment.

    Args:
        payment_id: UUID of the payment to refund.

    Returns:
        The updated Payment instance.

    Raises:
        PaymentNotFoundError: If payment does not exist.
    """
    logger.info("Refunding payment", payment_id=str(payment_id))

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist as e:
        logger.exception("Payment not found", payment_id=str(payment_id))
        error_msg = f"Payment {payment_id} not found"
        raise PaymentNotFoundError(error_msg) from e

    if payment.status == Payment.Status.REFUNDED:
        logger.warning("Payment already refunded", payment_id=str(payment_id))
        return payment

    if payment.status != Payment.Status.SUCCEEDED:
        logger.error(
            "Cannot refund payment with invalid status",
            payment_id=str(payment_id),
            status=payment.status,
        )
        error_msg = f"Cannot refund payment with status {payment.status}"
        raise InvalidAmountError(error_msg)

    payment.status = Payment.Status.REFUNDED
    payment.save()

    logger.info("Payment refunded successfully", payment_id=str(payment_id))
    return payment


def get_payment(payment_id: uuid.UUID) -> Payment:
    """Get a payment by ID.

    Args:
        payment_id: UUID of the payment.

    Returns:
        The Payment instance.

    Raises:
        PaymentNotFoundError: If payment does not exist.
    """
    try:
        return Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist as e:
        logger.exception("Payment not found", payment_id=str(payment_id))
        error_msg = f"Payment {payment_id} not found"
        raise PaymentNotFoundError(error_msg) from e


def get_payment_by_order(order_id: uuid.UUID) -> Payment:
    """Get a payment by order ID.

    Args:
        order_id: UUID of the order.

    Returns:
        The Payment instance.

    Raises:
        PaymentNotFoundError: If payment does not exist.
    """
    try:
        return Payment.objects.get(order_id=order_id)
    except Payment.DoesNotExist as e:
        logger.exception("Payment not found for order", order_id=str(order_id))
        error_msg = f"Payment for order {order_id} not found"
        raise PaymentNotFoundError(error_msg) from e
