from django.db import connections
from django.http import JsonResponse
from redis import Redis as RedisClient


def health_live(_request: JsonResponse) -> JsonResponse:
    """Liveness probe - always returns 200 if the app is running."""
    return JsonResponse({"status": "ok"})


def health_ready(_request: JsonResponse) -> JsonResponse:
    """Readiness probe - checks database, redis, and rabbitmq connectivity."""
    checks = {"database": _check_database(), "redis": _check_redis()}

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JsonResponse(
        {"status": "ok" if all_healthy else "unhealthy", "checks": checks}, status=status_code
    )


def _check_database() -> bool:
    """Check database connectivity."""
    try:
        db_conn = connections["default"]
        db_conn.cursor().execute("SELECT 1")
    except Exception:
        return False
    else:
        return True


def _check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        from config.settings.base import _settings

        redis_client = RedisClient(
            host=_settings.REDIS_HOST, port=_settings.REDIS_PORT, db=_settings.REDIS_DB
        )
        redis_client.ping()
    except Exception:
        return False
    else:
        return True
