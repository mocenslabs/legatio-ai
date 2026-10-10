"""
Views for the accounts app.
Handles authentication, 2FA, and user management endpoints.
"""

import urllib.parse

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    TwoFactorDisableSerializer,
    TwoFactorVerifySerializer,
    UserSerializer,
)
from apps.accounts.services.auth import (
    authenticate_user,
    generate_access_token,
    generate_refresh_token,
    refresh_access_token,
)
from apps.accounts.services.totp import (
    confirm_2fa_setup,
    disable_2fa,
    enable_2fa,
    verify_totp_code,
)
from apps.accounts.throttles import AuthAnonRateThrottle, SensitiveActionThrottle
from core.exceptions import InvalidCredentialsError, InvalidTOTPError


class RegisterView(APIView):
    """Register a new user."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request) -> Response:
        """Handle user registration."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        response = Response(
            {
                "access": access_token,
                "refresh": refresh_token,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.DEBUG is False,
            samesite="Lax",
            max_age=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
        )
        return response


class LoginView(APIView):
    """Authenticate a user."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request) -> Response:
        """Handle user login."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if user.two_factor_enabled:
            return Response(
                {
                    "requires_2fa": True,
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )

        access_token = generate_access_token(user, totp_verified=False)
        refresh_token = generate_refresh_token(user)

        response = Response(
            {
                "access": access_token,
                "refresh": refresh_token,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.DEBUG is False,
            samesite="Lax",
            max_age=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
        )
        return response


class TwoFactorVerifyLoginView(APIView):
    """Verify 2FA code during login."""

    permission_classes = [AllowAny]
    throttle_classes = [SensitiveActionThrottle]

    def post(self, request: Request) -> Response:
        """Handle 2FA verification during login."""
        email = request.data.get("email")
        password = request.data.get("password")
        code = request.data.get("code")

        if not all([email, password, code]):
            return Response(
                {"error": "Email, password, and code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_str = str(email)
        password_str = str(password)
        code_str = str(code)

        try:
            user = authenticate_user(email_str, password_str)
        except InvalidCredentialsError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.two_factor_enabled:
            return Response(
                {"error": "User does not have 2FA enabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_totp_code(user, code_str):
            return Response(
                {"error": "Invalid TOTP code."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = generate_access_token(user, totp_verified=True)
        refresh_token = generate_refresh_token(user)

        response = Response(
            {
                "access": access_token,
                "refresh": refresh_token,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.DEBUG is False,
            samesite="Lax",
            max_age=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
        )
        return response


class RefreshTokenView(APIView):
    """Refresh an access token."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request) -> Response:
        """Handle token refresh."""
        refresh_token = request.data.get("refresh") or request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token, user = refresh_access_token(refresh_token)
        except InvalidCredentialsError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "access": access_token,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Logout a user."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Handle user logout."""
        response = Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("refresh_token")
        return response


class TwoFactorEnableView(APIView):
    """Enable 2FA for a user."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveActionThrottle]

    def post(self, request: Request) -> Response:
        """Start 2FA setup."""
        secret, uri = enable_2fa(request.user)
        qr_code_url = (
            "https://chart.googleapis.com/chart?"
            f"chs=200x200&cht=qr&chl={urllib.parse.quote(uri)}"
        )
        return Response(
            {
                "secret": secret,
                "uri": uri,
                "qr_code_url": qr_code_url,
            },
            status=status.HTTP_200_OK,
        )


class TwoFactorConfirmView(APIView):
    """Confirm 2FA setup with a TOTP code."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveActionThrottle]

    def post(self, request: Request) -> Response:
        """Confirm 2FA setup."""
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]

        try:
            confirm_2fa_setup(request.user, code)
        except InvalidTOTPError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "2FA successfully enabled."},
            status=status.HTTP_200_OK,
        )


class TwoFactorDisableView(APIView):
    """Disable 2FA for a user."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveActionThrottle]

    def post(self, request: Request) -> Response:
        """Disable 2FA."""
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]

        try:
            disable_2fa(request.user, code)
        except InvalidTOTPError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "2FA successfully disabled."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Get or update current user information."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request: Request) -> Response:
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Change password for the authenticated user."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveActionThrottle]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )
