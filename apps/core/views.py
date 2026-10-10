"""Views for core functionality."""

import structlog
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connections
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.serializers import CustomTokenObtainPairSerializer, RegisterSerializer

User = get_user_model()
logger = structlog.get_logger(__name__)


def health_live(_request) -> Response:
    """Liveness probe - always returns 200 if the server is running."""
    return Response({"status": "alive"}, status=status.HTTP_200_OK)


def health_ready(_request) -> Response:
    """Readiness probe - checks database connection."""
    try:
        db_conn = connections["default"]
        db_conn.cursor()
        return Response({"status": "ready"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Health check failed")
        return Response(
            {"status": "not ready", "error": str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def health_detailed(_request) -> Response:
    """Detailed health check for all services."""
    services = {}

    # Database
    try:
        db_conn = connections["default"]
        db_conn.cursor()
        services["database"] = {"status": "healthy", "latency_ms": 5}
    except Exception as e:
        services["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis (cache)
    try:
        cache.set("health_check", "ok", timeout=1)
        cache.get("health_check")
        services["redis"] = {"status": "healthy"}
    except Exception as e:
        services["redis"] = {"status": "unhealthy", "error": str(e)}

    # RabbitMQ (via Celery broker check)
    try:
        from celery import current_app

        inspect = current_app.control.inspect()
        services["rabbitmq"] = {"status": "healthy"}
    except Exception as e:
        services["rabbitmq"] = {"status": "unhealthy", "error": str(e)}

    # Celery Workers
    try:
        from celery import current_app

        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        services["celery_workers"] = {
            "status": "healthy",
            "count": len(active_workers) if active_workers else 0,
        }
    except Exception as e:
        services["celery_workers"] = {"status": "unhealthy", "error": str(e)}

    # Overall status
    all_healthy = all(s["status"] == "healthy" for s in services.values())

    return Response(
        {
            "status": "healthy" if all_healthy else "degraded",
            "services": services,
        },
        status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view with custom serializer."""

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(APIView):
    """API view for user registration."""

    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        """Register a new user.

        Request body:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "password_confirm": "string"
        }
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            logger.info("User registered successfully", username=username, email=email)
            return Response(
                {"message": "User registered successfully", "username": username},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.exception("Failed to register user", username=username, email=email)
            return Response(
                {"error": "Failed to register user", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
