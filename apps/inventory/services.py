"""Services for inventory management."""

import uuid
from datetime import timedelta
from decimal import Decimal

import structlog
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import Product, StockReservation

logger = structlog.get_logger(__name__)


class InsufficientStockError(Exception):
    """Error raised when stock is insufficient."""


class ProductNotFoundError(Exception):
    """Error raised when product is not found."""


class ReservationNotFoundError(Exception):
    """Error raised when reservation is not found."""


def reserve_stock(
    order_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: int,
    ttl_minutes: int = 30,
) -> StockReservation:
    """Reserve stock for an order.

    Args:
        order_id: UUID of the order.
        product_id: UUID of the product.
        quantity: Quantity to reserve.
        ttl_minutes: Time to live for the reservation in minutes.

    Returns:
        The created StockReservation instance.

    Raises:
        ProductNotFoundError: If product does not exist.
        InsufficientStockError: If insufficient stock available.
    """
    logger.info(
        "Reserving stock",
        order_id=str(order_id),
        product_id=str(product_id),
        quantity=quantity,
    )

    try:
        product = Product.objects.select_for_update().get(id=product_id)
    except Product.DoesNotExist as e:
        logger.error("Product not found", product_id=str(product_id))
        raise ProductNotFoundError(f"Product {product_id} not found") from e

    if product.stock_quantity < quantity:
        logger.error(
            "Insufficient stock",
            product_id=str(product_id),
            available=product.stock_quantity,
            requested=quantity,
        )
        raise InsufficientStockError(
            f"Insufficient stock for product {product_id}. "
            f"Available: {product.stock_quantity}, Requested: {quantity}"
        )

    with transaction.atomic():
        product.stock_quantity -= quantity
        product.save()

        reservation = StockReservation.objects.create(
            id=uuid.uuid4(),
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            status=StockReservation.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )

    logger.info(
        "Stock reserved successfully",
        reservation_id=str(reservation.id),
        product_id=str(product_id),
        quantity=quantity,
    )
    return reservation


def release_stock(reservation_id: uuid.UUID) -> StockReservation:
    """Release a stock reservation.

    Args:
        reservation_id: UUID of the reservation to release.

    Returns:
        The updated StockReservation instance.

    Raises:
        ReservationNotFoundError: If reservation does not exist.
    """
    logger.info("Releasing stock reservation", reservation_id=str(reservation_id))

    try:
        reservation = StockReservation.objects.select_for_update().get(id=reservation_id)
    except StockReservation.DoesNotExist as e:
        logger.error("Reservation not found", reservation_id=str(reservation_id))
        raise ReservationNotFoundError(f"Reservation {reservation_id} not found") from e

    if reservation.status == StockReservation.Status.RELEASED:
        logger.warning("Reservation already released", reservation_id=str(reservation_id))
        return reservation

    try:
        product = Product.objects.select_for_update().get(id=reservation.product_id)
    except Product.DoesNotExist as e:
        logger.error("Product not found", product_id=str(reservation.product_id))
        raise ProductNotFoundError(f"Product {reservation.product_id} not found") from e

    with transaction.atomic():
        product.stock_quantity += reservation.quantity
        product.save()

        reservation.status = StockReservation.Status.RELEASED
        reservation.save()

    logger.info(
        "Stock released successfully",
        reservation_id=str(reservation_id),
        product_id=str(reservation.product_id),
        quantity=reservation.quantity,
    )
    return reservation


def confirm_reservation(reservation_id: uuid.UUID) -> StockReservation:
    """Confirm a stock reservation (order completed).

    Args:
        reservation_id: UUID of the reservation to confirm.

    Returns:
        The updated StockReservation instance.

    Raises:
        ReservationNotFoundError: If reservation does not exist.
    """
    logger.info("Confirming stock reservation", reservation_id=str(reservation_id))

    try:
        reservation = StockReservation.objects.select_for_update().get(id=reservation_id)
    except StockReservation.DoesNotExist as e:
        logger.error("Reservation not found", reservation_id=str(reservation_id))
        raise ReservationNotFoundError(f"Reservation {reservation_id} not found") from e

    if reservation.status == StockReservation.Status.CONFIRMED:
        logger.warning("Reservation already confirmed", reservation_id=str(reservation_id))
        return reservation

    reservation.status = StockReservation.Status.CONFIRMED
    reservation.save()

    logger.info(
        "Reservation confirmed successfully",
        reservation_id=str(reservation_id),
        product_id=str(reservation.product_id),
    )
    return reservation


def get_product(product_id: uuid.UUID) -> Product:
    """Get a product by ID.

    Args:
        product_id: UUID of the product.

    Returns:
        The Product instance.

    Raises:
        ProductNotFoundError: If product does not exist.
    """
    try:
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist as e:
        logger.error("Product not found", product_id=str(product_id))
        raise ProductNotFoundError(f"Product {product_id} not found") from e


def create_product(
    name: str,
    description: str,
    price: Decimal,
    stock_quantity: int,
) -> Product:
    """Create a new product.

    Args:
        name: Product name.
        description: Product description.
        price: Product price.
        stock_quantity: Initial stock quantity.

    Returns:
        The created Product instance.
    """
    logger.info("Creating product", name=name, price=str(price), stock_quantity=stock_quantity)

    product = Product.objects.create(
        id=uuid.uuid4(),
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
    )

    logger.info("Product created successfully", product_id=str(product.id))
    return product
