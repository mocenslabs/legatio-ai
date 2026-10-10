"""Health check views for Legatio AI."""

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def health_check(request: Request) -> Response:
    """
    Health check endpoint.

    Returns:
        JSON response with status "ok".
    """
    return Response({"status": "ok", "service": "legatio-backend"})


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def readiness_check(request: Request) -> Response:
    """
    Readiness check endpoint.

    Verifies that critical dependencies are available.

    Returns:
        JSON response with readiness status.
    """
    from django.db import connection

    checks = {
        "database": False,
        "cache": False,
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass

    # Check cache
    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", 10)
        checks["cache"] = cache.get("health_check") == "ok"
    except Exception:
        pass

    all_healthy = all(checks.values())

    return Response(
        {
            "status": "ok" if all_healthy else "degraded",
            "checks": checks,
        },
        status=200 if all_healthy else 503,
    )
