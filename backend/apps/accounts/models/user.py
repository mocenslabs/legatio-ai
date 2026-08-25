"""
User model for Legatio AI.

Custom User model extending AbstractBaseUser with UUID primary key.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager for User model with email as unique identifier."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields
    ) -> 'User':
        """
        Create and return a regular user with an email and password.

        Args:
            email: User's email address (used as username).
            password: User's password.
            **extra_fields: Additional fields for the user.

        Returns:
            The created User instance.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields
    ) -> 'User':
        """
        Create and return a superuser with an email and password.

        Args:
            email: Superuser's email address.
            password: Superuser's password.
            **extra_fields: Additional fields for the user.

        Returns:
            The created superuser instance.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for Legatio AI.

    Uses email as the unique identifier instead of username.
    Extends AbstractBaseUser and PermissionsMixin for full auth support.
    """

    id: models.UUIDField = models.UUIDField(  # type: ignore[assignment]
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )
    email: models.EmailField = models.EmailField(  # type: ignore[assignment]
        unique=True,
        max_length=255,
        db_index=True,
        help_text='User email address (used as login identifier)',
    )
    first_name: models.CharField = models.CharField(  # type: ignore[assignment]
        max_length=100,
        blank=True,
        default='',
    )
    last_name: models.CharField = models.CharField(  # type: ignore[assignment]
        max_length=100,
        blank=True,
        default='',
    )
    is_active: models.BooleanField = models.BooleanField(  # type: ignore[assignment]
        default=True,
        help_text='Designates whether this user should be treated as active.',
    )
    is_staff: models.BooleanField = models.BooleanField(  # type: ignore[assignment]
        default=False,
        help_text='Designates whether the user can log into the admin site.',
    )
    is_verified: models.BooleanField = models.BooleanField(  # type: ignore[assignment]
        default=False,
        help_text='Designates whether the user has verified their email.',
    )
    two_factor_enabled: models.BooleanField = models.BooleanField(  # type: ignore[assignment]
        default=False,
        help_text='Designates whether the user has 2FA enabled.',
    )
    totp_secret: models.CharField = models.CharField(  # type: ignore[assignment]
        max_length=32,
        null=True,
        blank=True,
        help_text='Encrypted TOTP secret for 2FA.',
    )
    preferred_language: models.CharField = models.CharField(  # type: ignore[assignment]
        max_length=10,
        default='en',
        help_text='User preferred language (ISO 639-1).',
    )
    preferred_timezone: models.CharField = models.CharField(  # type: ignore[assignment]
        max_length=50,
        default='UTC',
        help_text='User preferred timezone (IANA timezone).',
    )
    last_login: models.DateTimeField = models.DateTimeField(  # type: ignore[assignment]
        null=True,
        blank=True,
    )
    date_joined: models.DateTimeField = models.DateTimeField(  # type: ignore[assignment]
        auto_now_add=True,
        help_text='Timestamp when the user was created.',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'legatio_accounts_user'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['-date_joined'], name='idx_user_date_joined'),
        ]

    def __str__(self) -> str:
        """Return string representation of the user."""
        return self.email

    def get_full_name(self) -> str:
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email

    def get_short_name(self) -> str:
        """Return the short name for the user."""
        return self.first_name or self.email
