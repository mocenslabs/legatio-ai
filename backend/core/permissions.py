"""
Custom permissions for Legatio AI.

This module provides reusable permission classes for DRF views.
All permissions follow the fail-safe principle: deny by default
when in doubt.

Reference: 02-ARCHITECTURE.md Section 11.2
"""

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.

    Read permissions (GET, HEAD, OPTIONS) are allowed for any
    authenticated request. Write permissions (POST, PUT, PATCH, DELETE)
    are only allowed to the owner of the object.

    The object must have an ``owner`` attribute that references a User.
    If the object has no ``owner`` attribute, write access is denied
    (fail-safe default).
    """

    message = "You do not have permission to modify this object."

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: Any,
    ) -> bool:
        """
        Check if the request user has permission on the object.

        Args:
            request: The current HTTP request.
            view: The view being accessed.
            obj: The object being accessed (expected to have an
                ``owner`` attribute).

        Returns:
            True if permission is granted, False otherwise.
        """
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only allowed to the owner.
        # Use getattr with default None for fail-safe behavior
        # when the object doesn't have an 'owner' attribute.
        owner = getattr(obj, "owner", None)
        return bool(owner is not None and owner == request.user)
