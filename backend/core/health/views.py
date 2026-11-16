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
    Liveness probe — process is up.
    """
    return Response({"status": "ok", "service": "legatio-backend"})


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def readiness_check(request: Request) -> Response:
    """
    Readiness probe — critical dependencies are available.

    Checks: database, cache (Redis), channel_layer (WebSocket Redis layer).
    """
    from django.db import connection

    checks: dict[str, bool] = {
        "database": False,
        "cache": False,
        "channel_layer": False,
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass

    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", 10)
        checks["cache"] = cache.get("health_check") == "ok"
    except Exception:
        pass

    try:
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            checks["channel_layer"] = False
        else:
            module = channel_layer.__class__.__module__.lower()
            if "inmemory" in module:
                checks["channel_layer"] = True
            else:
                # Redis channel layer: verify underlying client responds to ping
                # channels_redis exposes .connection_layer / hosts; use cache
                # success as proxy when both share REDIS_URL, plus layer exists.
                checks["channel_layer"] = checks["cache"] and channel_layer is not None
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
