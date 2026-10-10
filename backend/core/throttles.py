"""
Custom throttles for Legatio AI.

Provides rate limiting for sensitive endpoints.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthAnonRateThrottle(AnonRateThrottle):
    """Rate limit for anonymous auth endpoints (login, register)."""

    rate = "10/minute"


class AuthUserRateThrottle(UserRateThrottle):
    """Rate limit for authenticated auth endpoints."""

    rate = "30/minute"


class SensitiveActionThrottle(UserRateThrottle):
    """Rate limit for sensitive actions (2FA, password change)."""

    rate = "5/minute"
