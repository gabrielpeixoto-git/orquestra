"""URLs for core functionality."""

from django.urls import path

from apps.core.views import CustomTokenObtainPairView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
]
