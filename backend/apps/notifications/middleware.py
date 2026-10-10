"""JWT authentication middleware for WebSocket connections."""

import logging
from typing import Any
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from core.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):  # type: ignore[misc]
    """JWT authentication middleware for WebSocket via query string."""

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> Any:
        query_string = scope.get("query_string", b"")
        if isinstance(query_string, bytes):
            query_string = query_string.decode("utf-8")

        query_params = parse_qs(query_string)
        token_list = query_params.get("token", [])
        token = token_list[0] if token_list else None

        if token:
            try:
                user = await self._get_user_from_token(token)
                scope["user"] = user
                logger.info(f"WebSocket authenticated for user {user.id}")
            except Exception as e:
                logger.warning(f"JWT authentication failed: {e}")
                scope["user"] = AnonymousUser()
        else:
            logger.warning("No JWT token provided")
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async  # type: ignore[misc]
    def _get_user_from_token(self, token: str) -> Any:
        """Extract user from JWT token using core.authentication."""
        auth = JWTAuthentication()
        try:
            validated_token = auth.get_validated_token(token.encode())
            user = auth.get_user(validated_token)
            if user is None:
                return AnonymousUser()
            return user
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return AnonymousUser()
