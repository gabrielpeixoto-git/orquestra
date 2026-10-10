from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("orders/", include("apps.orders.urls")),
    path("auth/", include("apps.core.urls")),
    path("staff/", include("apps.outbox.urls")),
]
