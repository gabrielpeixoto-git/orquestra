"""URL configuration for dashboard app."""

from django.urls import path

from apps.dashboard import sse_views, views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("orders/", views.orders, name="orders"),
    path("orders/<uuid:order_id>/", views.order_detail, name="order_detail"),
    path("dead-letters/", views.dead_letters, name="dead_letters"),
    path(
        "dead-letters/<uuid:dead_letter_id>/replay/",
        views.replay_dead_letter,
        name="replay_dead_letter",
    ),
    path(
        "dead-letters/<uuid:dead_letter_id>/discard/",
        views.discard_dead_letter,
        name="discard_dead_letter",
    ),
    path("laboratory/", views.laboratory, name="laboratory"),
    path("laboratory/generate-order/", views.generate_order, name="generate_order"),
    path("laboratory/inject-failure/", views.inject_failure, name="inject_failure"),
    path("health/", views.health, name="health"),
    path("sse/orders/", sse_views.sse_orders, name="sse_orders"),
]
