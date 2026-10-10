"""Views for dashboard app."""

from uuid import UUID

import requests
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from apps.orders.models import Order, OrderItem
from apps.outbox.models import DeadLetterMessage
from apps.outbox.services_deadletter import mark_dead_letter_discarded, mark_dead_letter_replayed


@csrf_exempt
def generate_order(request):
    """Generate a test order."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        import uuid

        from apps.inventory.models import Product

        # Get a real product or create one
        product = Product.objects.first()
        if not product:
            product = Product.objects.create(
                id=uuid.uuid4(),
                name="Test Product",
                description="A test product for laboratory",
                price=100.00,
                stock_quantity=100,
            )

        customer_id = uuid.uuid4()
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=customer_id,
            total_amount=product.price,
            status=Order.Status.PENDING,
        )

        # Create order item with real product
        OrderItem.objects.create(
            id=uuid.uuid4(),
            order=order,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            total_price=product.price,
        )

        return JsonResponse(
            {"success": True, "message": "Order created", "order_id": str(order.id)}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def overview(request):
    """Overview page with KPIs and pipeline visualization."""
    # KPIs
    total_orders = Order.objects.count()
    confirmed_orders = Order.objects.filter(status=Order.Status.CONFIRMED).count()
    failed_orders = Order.objects.filter(status=Order.Status.CANCELLED).count()
    dead_letters = DeadLetterMessage.objects.filter(status=DeadLetterMessage.Status.PENDING).count()

    success_rate = (confirmed_orders / total_orders * 100) if total_orders > 0 else 0

    # Status distribution
    status_counts = Order.objects.values("status").annotate(count=Count("id")).order_by("status")

    return render(
        request,
        "dashboard/overview.html",
        {
            "total_orders": total_orders,
            "confirmed_orders": confirmed_orders,
            "failed_orders": failed_orders,
            "dead_letters": dead_letters,
            "success_rate": round(success_rate, 1),
            "status_counts": list(status_counts),
        },
    )


def orders(request):
    """Orders list page with live table and filters."""
    status_filter = request.GET.get("status")
    search = request.GET.get("search")

    orders_qs = Order.objects.all().order_by("-created_at")

    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    if search:
        orders_qs = orders_qs.filter(id__icontains=search)

    # Check if this is an HTMX request for table body only
    if request.headers.get("HX-Request"):
        return render(
            request,
            "dashboard/orders_table_body.html",
            {
                "orders": orders_qs[:50],  # Limit to 50 for performance
            },
        )

    return render(
        request,
        "dashboard/orders.html",
        {
            "orders": orders_qs[:50],  # Limit to 50 for performance
            "status_filter": status_filter,
            "search": search,
        },
    )


def order_detail(request, order_id: UUID):
    """Order detail page with timeline."""
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return render(request, "dashboard/404.html", status=404)

    # Get outbox messages for timeline
    from apps.outbox.models import OutboxMessage

    messages = OutboxMessage.objects.filter(aggregate_id=order_id).order_by("created_at")

    return render(
        request,
        "dashboard/order_detail.html",
        {"order": order, "messages": messages},
    )


def dead_letters(request):
    """Dead letters page with replay/discard actions."""
    dead_letters = DeadLetterMessage.objects.filter(
        status=DeadLetterMessage.Status.PENDING
    ).order_by("-created_at")

    # Check if this is an HTMX request for table body only
    if request.headers.get("HX-Request"):
        return render(
            request,
            "dashboard/dead_letters_table_body.html",
            {"dead_letters": dead_letters},
        )

    return render(request, "dashboard/dead_letters.html", {"dead_letters": dead_letters})


@csrf_exempt
def replay_dead_letter(request, dead_letter_id: UUID):
    """Replay a dead letter message."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        mark_dead_letter_replayed(dead_letter_id)
        return JsonResponse({"success": True, "message": "Dead letter replayed"})
    except DeadLetterMessage.DoesNotExist:
        return JsonResponse({"error": "Dead letter not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def discard_dead_letter(request, dead_letter_id: UUID):
    """Discard a dead letter message."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        mark_dead_letter_discarded(dead_letter_id)
        return JsonResponse({"success": True, "message": "Dead letter discarded"})
    except DeadLetterMessage.DoesNotExist:
        return JsonResponse({"error": "Dead letter not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def laboratory(request):
    """Laboratory page for generating orders and injecting failures."""
    return render(request, "dashboard/laboratory.html")


def health(request):
    """Health page with service status."""
    try:
        # Get detailed health from API
        response = requests.get("http://localhost:8000/health/detailed/", timeout=2)
        health_data = response.json() if response.status_code == 200 else None
    except Exception:
        health_data = None

    # Check if this is an HTMX request for content only
    if request.headers.get("HX-Request"):
        return render(
            request,
            "dashboard/health_content.html",
            {"health_data": health_data},
        )

    return render(request, "dashboard/health.html", {"health_data": health_data})


@csrf_exempt
def inject_failure(request):
    """Inject a failure for testing DLQ."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    failure_type = request.POST.get("failure_type")

    try:
        import uuid

        from apps.outbox.services_deadletter import create_dead_letter

        correlation_id = uuid.uuid4()

        if failure_type == "payment_timeout":
            # Create a fake dead letter for payment timeout
            dead_letter = create_dead_letter(
                queue_name="payments",
                message_type="PaymentFailed",
                payload={"order_id": str(uuid.uuid4()), "amount": 100.00},
                error_message="Payment gateway timeout (simulated)",
                correlation_id=correlation_id,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Payment timeout injected",
                    "dead_letter_id": str(dead_letter.id),
                }
            )

        if failure_type == "stock_error":
            # Create a fake dead letter for stock error
            dead_letter = create_dead_letter(
                queue_name="inventory",
                message_type="StockReservationFailed",
                payload={"order_id": str(uuid.uuid4()), "product_id": str(uuid.uuid4())},
                error_message="Stock reservation error (simulated)",
                correlation_id=correlation_id,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Stock error injected",
                    "dead_letter_id": str(dead_letter.id),
                }
            )

        return JsonResponse({"error": "Invalid failure type"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
