from django.urls import path

from apps.orders.views import CreateOrderView, OrderDetailView

urlpatterns = [
    path("", CreateOrderView.as_view(), name="order-create"),
    path("<uuid:order_id>/", OrderDetailView.as_view(), name="order-detail"),
]
