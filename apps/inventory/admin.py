from django.contrib import admin

from .models import Product, StockReservation


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "price", "stock_quantity"]
    search_fields = ["id", "name"]


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order_id",
        "product_id",
        "quantity",
        "status",
        "created_at",
        "expires_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["id", "order_id", "product_id"]
