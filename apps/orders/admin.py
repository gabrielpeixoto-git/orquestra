from django.contrib import admin

from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer_id", "total_amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["id", "customer_id"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "product_id", "quantity", "unit_price", "total_price"]
    list_filter = ["order"]
    search_fields = ["id", "product_id"]
