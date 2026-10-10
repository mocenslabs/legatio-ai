"""
Custom JWT authentication for Legatio AI.
"""

from typing import Any, cast

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request


class JWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        return (user, validated_token)

    def authenticate_header(self, request: Request) -> str:
        return self.keyword

    def get_header(self, request: Request) -> bytes | None:
        header = request.META.get("HTTP_AUTHORIZATION")
        if isinstance(header, str):
            header = header.encode("iso-8859-1")
        return header

    def get_raw_token(self, header: bytes) -> bytes | None:
        parts = header.split()
        if len(parts) != 2 or parts[0].decode() != self.keyword:
            return None
        return parts[1]

    def get_validated_token(self, raw_token: bytes) -> dict[str, Any]:
        try:
            token_str = raw_token.decode()
        except UnicodeError as exc:
            raise exceptions.AuthenticationFailed(_("Invalid token encoding.")) from exc

        try:
            payload = jwt.decode(
                token_str,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.AuthenticationFailed(_("Token has expired.")) from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed(_("Invalid token.")) from exc

        if payload.get("token_type") != "access":
            raise exceptions.AuthenticationFailed(_("Token type must be 'access'."))

        return cast(dict[str, Any], payload)

    def get_user(self, validated_token: dict[str, Any]) -> Any:
        try:
            user_id = validated_token["user_id"]
        except KeyError as exc:
            raise exceptions.AuthenticationFailed(
                _("Token contained no recognizable user identification.")
            ) from exc

        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist as exc:
            raise exceptions.AuthenticationFailed(_("User not found.")) from exc

        if not user.is_active:
            raise exceptions.AuthenticationFailed(_("User account is disabled."))

        return user


class JWTAuthenticationWith2FA(JWTAuthentication):
    def get_user(self, validated_token: dict[str, Any]) -> Any:
        user = super().get_user(validated_token)

        if user.two_factor_enabled and not validated_token.get("totp_verified"):
            raise exceptions.AuthenticationFailed(_("Two-factor authentication required."))
        return user
