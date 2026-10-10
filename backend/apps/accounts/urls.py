"""URL configuration for the accounts app."""

from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("login/2fa/", views.TwoFactorVerifyLoginView.as_view(), name="login-2fa"),
    path("refresh/", views.RefreshTokenView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # 2FA
    path("2fa/enable/", views.TwoFactorEnableView.as_view(), name="2fa-enable"),
    path("2fa/confirm/", views.TwoFactorConfirmView.as_view(), name="2fa-confirm"),
    path("2fa/disable/", views.TwoFactorDisableView.as_view(), name="2fa-disable"),
    # User
    path("me/", views.MeView.as_view(), name="me"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
]
