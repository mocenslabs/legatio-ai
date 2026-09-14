"""Authentication API views."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView

from apps.accounts.models import User
from apps.accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    TokenRefreshSerializer,
    TwoFactorEnableSerializer,
    TwoFactorVerifySerializer,
)
from apps.accounts.services import AuthService
from apps.accounts.services.auth_service import (
    AuthServiceError,
    InvalidTwoFactorCodeError,
    TwoFactorAlreadyEnabledError,
)


class RegisterView(APIView):
    """API view for user registration."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthService.register_user(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                first_name=serializer.validated_data.get("first_name", ""),
                last_name=serializer.validated_data.get("last_name", ""),
            )

            tokens = AuthService.generate_tokens(user)

            return Response(
                {
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )
        except AuthServiceError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(APIView):
    """API view for user login."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        if user.two_factor_enabled:
            return Response(
                {
                    "requires_2fa": True,
                    "user_id": str(user.id),
                },
                status=status.HTTP_200_OK,
            )

        tokens = AuthService.generate_tokens(user)

        return Response(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(SimpleJWTTokenRefreshView):
    """API view for token refresh."""

    serializer_class = TokenRefreshSerializer  # type: ignore[assignment]


class TwoFactorEnableView(APIView):
    """API view for enabling 2FA."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = TwoFactorEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = AuthService.enable_two_factor(request.user)  # type: ignore[arg-type]
            return Response(result, status=status.HTTP_200_OK)
        except TwoFactorAlreadyEnabledError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TwoFactorVerifyView(APIView):
    """API view for verifying 2FA code."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.data.get("user_id")
        code = serializer.validated_data["code"]

        if not user_id:
            return Response(
                {"error": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            AuthService.verify_two_factor_code(user, code)
            tokens = AuthService.generate_tokens(user)

            return Response(
                {
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        except InvalidTwoFactorCodeError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
