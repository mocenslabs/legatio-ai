"""JWT authentication middleware for WebSocket connections.

This module provides a Channels middleware that authenticates WebSocket
connections using JWT tokens passed as query parameters. This aligns
WebSocket authentication with the REST API's SimpleJWT authentication.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


@database_sync_to_async
def _get_user_from_token(token_string: str) -> Any:
    """Validate a JWT token and return the corresponding user.

    Args:
        token_string: The JWT access token string.

    Returns:
        The authenticated User instance, or AnonymousUser if invalid.
    """
    try:
        # NOTE: SimpleJWT's type stubs incorrectly annotate AccessToken's
        # constructor as accepting Token | None, but it accepts a raw string
        # at runtime. The type: ignore is required due to the stub bug.
        token = AccessToken(token_string)  # type: ignore[arg-type]
        user_id = token["user_id"]

        from apps.accounts.models import User

        return User.objects.get(id=user_id)
    except TokenError as e:
        logger.warning("Invalid JWT token for WebSocket: %s", str(e))
        return AnonymousUser()
    except Exception as e:
        logger.exception("Error validating WebSocket JWT token: %s", str(e))
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Channels middleware for JWT authentication of WebSocket connections.

    Extracts the JWT token from the WebSocket query string (passed as
    ?token=<jwt>), validates it using SimpleJWT, and populates the scope
    with the authenticated user. Unauthenticated connections receive
    AnonymousUser and are rejected by the consumer.

    If the scope already contains an authenticated user (e.g., set by
    tests or another middleware), it is respected and not overwritten.

    Usage:
        Connect with: ws://host/ws/notifications/?token=<access_token>
    """

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Any],
        send: Callable[..., Any],
    ) -> Any:
        """Process the WebSocket connection and authenticate via JWT.

        Args:
            scope: The ASGI connection scope.
            receive: The receive callable.
            send: The send callable.

        Returns:
            The result of the inner application call.
        """
        # If scope already has an authenticated user, respect it (useful for tests)
        existing_user = scope.get("user")
        if existing_user is not None and hasattr(existing_user, "is_authenticated"):
            if existing_user.is_authenticated:
                logger.debug("WebSocket connection already authenticated")
                return await super().__call__(scope, receive, send)

        # Otherwise, try to authenticate via JWT token in query string
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token_list = query_params.get("token", [])
        token = token_list[0] if token_list else None

        if token:
            scope["user"] = await _get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()
            logger.debug("WebSocket connection without token")

        return await super().__call__(scope, receive, send)
