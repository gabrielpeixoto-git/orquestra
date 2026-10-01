from django.core.management.base import BaseCommand
from django.db import connections
from redis import Redis as RedisClient


class Command(BaseCommand):
    """Check health of dependencies."""

    def handle(self, *_args: str, **_options: str) -> None:
        """Execute health checks."""
        checks = {
            "database": self._check_database(),
            "redis": self._check_redis(),
        }

        all_healthy = all(checks.values())

        for service, status in checks.items():
            self.stdout.write(f"{service}: {'OK' if status else 'FAIL'}")

        if not all_healthy:
            raise SystemExit(1)

    def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            db_conn = connections["default"]
            db_conn.cursor().execute("SELECT 1")
        except Exception:
            return False
        else:
            return True

    def _check_redis(self) -> bool:
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
