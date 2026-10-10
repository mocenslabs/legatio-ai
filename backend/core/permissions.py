"""
Custom permissions for Legatio AI.
Provides object-level permissions to ensure users can only access
their own resources.
Source: 02-ARCHITECTURE.md Section 11.2
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission that only allows owners of an object to edit it.
    Assumes the model instance has an `owner` or `user` attribute.
    """

    message = "You do not have permission to perform this action."

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return self._is_owner(request.user, obj)

    def _is_owner(self, user: object, obj: object) -> bool:
        """Check if the user is the owner of the object."""
        if hasattr(obj, "owner"):
            return obj.owner == user  # type: ignore[no-any-return]
        if hasattr(obj, "user"):
            return obj.user == user  # type: ignore[no-any-return]
        return False


class IsOwner(permissions.BasePermission):
    """
    Object-level permission that only allows owners of an object to access it.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        return self._is_owner(request.user, obj)

    def _is_owner(self, user: object, obj: object) -> bool:
        """Check if the user is the owner of the object."""
        if hasattr(obj, "owner"):
            return obj.owner == user  # type: ignore[no-any-return]
        if hasattr(obj, "user"):
            return obj.user == user  # type: ignore[no-any-return]
        return False


class IsAdminUser(permissions.BasePermission):
    """Allows access only to admin users."""

    message = "Admin access required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsVerifiedUser(permissions.BasePermission):
    """Allows access only to verified users."""

    message = "Email verification required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_verified)


class Requires2FA(permissions.BasePermission):
    """
    Requires 2FA verification for users who have 2FA enabled.
    """

    message = "Two-factor authentication required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.two_factor_enabled:
            return True
        auth = request.auth
        if isinstance(auth, dict):
            return bool(auth.get("totp_verified", False))
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access to the owner of an object or to admin users.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        if request.user and request.user.is_staff:
            return True
        if hasattr(obj, "owner"):
            return obj.owner == request.user  # type: ignore[no-any-return]
        if hasattr(obj, "user"):
            return obj.user == request.user  # type: ignore[no-any-return]
        return False
