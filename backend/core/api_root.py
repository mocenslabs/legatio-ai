"""API root — discoverability for humans and clients."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request: Request) -> Response:
    """
    Minimal index of public API entry points (v1).
    """
    base = request.build_absolute_uri("/api/v1/")
    return Response(
        {
            "name": "Legatio AI API",
            "version": "v1",
            "documentation": {
                "schema": f"{base}schema/",
                "swagger": f"{base}docs/",
                "redoc": f"{base}redoc/",
            },
            "endpoints": {
                "health": f"{base}health/",
                "ready": f"{base}ready/",
                "auth": {
                    "register": f"{base}auth/register/",
                    "login": f"{base}auth/login/",
                    "refresh": f"{base}auth/refresh/",
                    "me": f"{base}auth/me/",
                },
                "organizations": f"{base}organizations/",
                "billing": {
                    "plans": f"{base}billing/plans/",
                },
                "agents": f"{base}agents/",
                "constitutions": f"{base}constitutions/",
                "negotiations": f"{base}negotiations/",
                "approvals": f"{base}approvals/",
                "agreements": f"{base}agreements/",
                "audit": f"{base}audit/",
            },
        }
    )
