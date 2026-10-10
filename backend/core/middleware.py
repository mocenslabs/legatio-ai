"""
Custom middleware for Legatio AI.
Provides request-level functionality like correlation IDs,
timing, and audit logging.
"""

import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("legatio.middleware")


class CorrelationIdMiddleware:
    """Adds a unique correlation ID to each request for tracing."""

    HEADER_NAME = "X-Correlation-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.META.get(f"HTTP_{self.HEADER_NAME.upper().replace('-', '_')}")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.correlation_id = correlation_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response[self.HEADER_NAME] = correlation_id
        return response


class RequestTimingMiddleware:
    """Logs the time taken to process each request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start_time) * 1000)

        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.id)

        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
            },
        )
        response["X-Request-Duration-Ms"] = str(duration_ms)
        return response


class SecurityHeadersMiddleware:
    """Adds security headers to all responses."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
