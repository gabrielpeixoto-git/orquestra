"""Views for dashboard app."""

import random
from uuid import UUID

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.orders.models import Order, OrderItem
from apps.outbox.models import DeadLetterMessage
from apps.outbox.services_deadletter import mark_dead_letter_discarded, mark_dead_letter_replayed


def dashboard_login(request):
    """Custom login view for dashboard."""
    if request.user.is_authenticated:
        return redirect("dashboard:overview")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard:overview")
        else:
            return render(
                request,
                "dashboard/login.html",
                {"error": "Usuário ou senha inválidos"},
            )

    return render(request, "dashboard/login.html")


def dashboard_logout(request):
    """Logout view for dashboard."""
    logout(request)
    return redirect("dashboard:login")


@login_required
def generate_order(request):
    """Generate a test order."""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

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
        customer_names = [
            "Maria Santos",
            "João Silva",
            "Ana Costa",
            "Pedro Oliveira",
            "Juliana Ferreira",
            "Lucas Rodrigues",
            "Camila Almeida",
            "Rafael Pereira",
            "Fernanda Lima",
            "Carlos Mendes",
        ]
        customer_name = random.choice(customer_names)
        order = Order.objects.create(
            id=uuid.uuid4(),
            customer_id=customer_id,
            customer_name=customer_name,
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
            {"success": True, "message": "Pedido criado", "order_id": str(order.id)}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def overview(request):
    """Overview page with KPIs and pipeline visualization."""
    # KPIs
    total_orders = Order.objects.count()
    confirmed_orders = Order.objects.filter(status=Order.Status.CONFIRMED).count()
    failed_orders = Order.objects.filter(status=Order.Status.CANCELLED).count()
    dead_letters = DeadLetterMessage.objects.filter(status=DeadLetterMessage.Status.PENDING).count()

    # Calculate total revenue from confirmed orders
    from django.db.models import Sum

    revenue = (
        Order.objects.filter(status=Order.Status.CONFIRMED).aggregate(total=Sum("total_amount"))[
            "total"
        ]
        or 0
    )

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
            "revenue": round(revenue, 2),
            "success_rate": round(success_rate, 1),
            "status_counts": list(status_counts),
        },
    )


@login_required
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


@login_required
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


@login_required
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


@login_required
def replay_dead_letter(request, dead_letter_id: UUID):
    """Replay a dead letter message."""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    try:
        mark_dead_letter_replayed(dead_letter_id)
        return JsonResponse({"success": True, "message": "Mensagem reprocessada"})
    except DeadLetterMessage.DoesNotExist:
        return JsonResponse({"error": "Mensagem não encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def discard_dead_letter(request, dead_letter_id: UUID):
    """Discard a dead letter message."""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    try:
        mark_dead_letter_discarded(dead_letter_id)
        return JsonResponse({"success": True, "message": "Mensagem descartada"})
    except DeadLetterMessage.DoesNotExist:
        return JsonResponse({"error": "Mensagem não encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def laboratory(request):
    """Laboratory page for generating orders and injecting failures."""
    return render(request, "dashboard/laboratory.html")


@login_required
def health(request):
    """Health page with service status."""
    from apps.core.views import health_detailed

    # Call health service directly
    response = health_detailed(request)
    health_data = response.data

    # For debugging: return JSON if requested
    if request.GET.get("format") == "json":
        from django.http import JsonResponse

        return JsonResponse(health_data)

    return render(request, "dashboard/health.html", {"health_data": health_data})


@login_required
def inject_failure(request):
    """Inject a failure for testing DLQ."""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

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
                error_message="Timeout do gateway de pagamento (simulado)",
                correlation_id=correlation_id,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Timeout de pagamento injetado",
                    "dead_letter_id": str(dead_letter.id),
                }
            )

        if failure_type == "stock_error":
            # Create a fake dead letter for stock error
            dead_letter = create_dead_letter(
                queue_name="inventory",
                message_type="StockReservationFailed",
                payload={"order_id": str(uuid.uuid4()), "product_id": str(uuid.uuid4())},
                error_message="Erro de reserva de estoque (simulado)",
                correlation_id=correlation_id,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Erro de estoque injetado",
                    "dead_letter_id": str(dead_letter.id),
                }
            )

        return JsonResponse({"error": "Tipo de falha inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
