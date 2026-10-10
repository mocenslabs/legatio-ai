"""
Custom managers for the accounts app.
Provides UserManager for creating User instances with proper
password hashing and field defaults.
Source: 03-DATA-MODEL.md Section 6.1
"""

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import BaseUserManager

if TYPE_CHECKING:
    from apps.accounts.models import User


class UserManager(BaseUserManager["User"]):
    """
    Custom manager for User model.
    Uses email as the unique identifier instead of username.
    """

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_verified", False)
        extra_fields.setdefault("two_factor_enabled", False)
        extra_fields.setdefault("preferred_language", "en")
        extra_fields.setdefault("preferred_timezone", "UTC")

        from apps.accounts.models import User

        user = User(email=email, **extra_fields)
        if password is not None:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Create and return a superuser with all permissions.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
