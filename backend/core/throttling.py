"""Custom DRF throttle classes for API rate limiting.

This module provides custom throttle classes that enforce rate limits
on API requests to protect against abuse and ensure fair usage. Rates
are configured via the DEFAULT_THROTTLE_RATES setting.
"""

from __future__ import annotations

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """Throttle for short bursts of requests per authenticated user.

    Limits the number of requests a user can make within a short window
    (e.g., per minute) to prevent burst abuse.
    """

    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """Throttle for sustained request volume per authenticated user.

    Limits the total number of requests a user can make over a longer
    window (e.g., per day) to ensure fair usage over time.
    """

    scope = "sustained"


class AnonBurstRateThrottle(AnonRateThrottle):
    """Throttle for anonymous request bursts.

    Limits unauthenticated requests to protect public endpoints such
    as token acquisition from brute-force attempts.
    """

    scope = "anon_burst"
