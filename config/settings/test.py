SECRET_KEY = "test-secret-key"
DEBUG = True

from .base import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.db.sqlite3",  # noqa: F405
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

STATIC_ROOT = BASE_DIR / "test_staticfiles"  # noqa: F405

# Use dummy cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
