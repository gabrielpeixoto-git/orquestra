from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order_id", "amount", "status", "gateway_transaction_id", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["id", "order_id", "gateway_transaction_id"]
