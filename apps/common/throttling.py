from rest_framework.throttling import UserRateThrottle


class AIUserThrottle(UserRateThrottle):
    """Per-user AI throttle, separate from the general API throttle."""

    scope = "ai"
