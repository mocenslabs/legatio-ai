"""Accounts API URLs.

This module defines the URL routing for the accounts app API endpoints.
"""

from __future__ import annotations

from django.urls import path

from apps.accounts.views import (
    LoginView,
    RegisterView,
    TokenRefreshView,
    TwoFactorEnableView,
    TwoFactorVerifyView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("2fa/enable/", TwoFactorEnableView.as_view(), name="2fa_enable"),
    path("2fa/verify/", TwoFactorVerifyView.as_view(), name="2fa_verify"),
]
