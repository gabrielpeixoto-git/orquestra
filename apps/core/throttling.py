"""Custom throttling classes using Redis."""

from django.core.cache import caches
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonRateThrottleRedis(AnonRateThrottle):
    """Anonymous rate throttle using Redis."""

    cache = caches["default"]


class UserRateThrottleRedis(UserRateThrottle):
    """User rate throttle using Redis."""

    cache = caches["default"]
