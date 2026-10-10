"""
DRF Mixins for ownership and filtering.
These mixins ensure that users can only access their own resources.
They must be used in all ViewSets that handle user-owned resources.
Source: 02-ARCHITECTURE.md Section 11.2
Source: 00-INDEX.md Section 2.5 (Aislamiento por usuario)
"""

from typing import Any

from rest_framework.exceptions import NotFound


class OwnedQuerySetMixin:
    """
    Mixin that filters querysets by the current user.
    Assumes the model has an `owner` field pointing to User.
    """

    request: Any
    kwargs: dict[str, Any]

    def get_queryset(self) -> Any:
        """Filter queryset to only include objects owned by the current user."""
        queryset = super().get_queryset()  # type: ignore[misc]
        if not hasattr(self, "request") or self.request is None:
            return queryset.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        return queryset.filter(owner=user)


class OwnedObjectMixin:
    """
    Mixin that verifies ownership on object-level operations.
    Used for retrieve, update, partial_update, and destroy actions.
    """

    request: Any
    kwargs: dict[str, Any]
    lookup_field: str = "pk"
    lookup_url_kwarg: str | None = None

    def get_queryset(self) -> Any:
        """Get the base queryset. Must be provided by the ViewSet."""
        raise NotImplementedError

    def check_object_permissions(self, request: Any, obj: Any) -> None:
        """Check object permissions. Must be provided by the ViewSet."""
        raise NotImplementedError

    def get_object(self) -> Any:
        """
        Retrieve object and verify ownership.
        Returns:
            The object if the user owns it.
        Raises:
            NotFound: If the object does not exist or user doesn't own it.
        """
        queryset = self.get_queryset()
        if hasattr(self, "request") and self.request is not None:
            user = self.request.user
            if user and user.is_authenticated:
                queryset = queryset.filter(owner=user)

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            f"Expected view {self.__class__.__name__} to be called with a URL "
            f"keyword argument named '{lookup_url_kwarg}'. Fix your URL conf, or "
            f"set the `.lookup_field` attribute on the view correctly."
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = queryset.filter(**filter_kwargs).first()
        if obj is None:
            raise NotFound("Resource not found.")

        self.check_object_permissions(self.request, obj)
        return obj


class UserScopedQuerySetMixin:
    """
    Mixin for models where ownership is via `user` field (not `owner`).
    Used for UserProfile and similar models.
    """

    request: Any
    kwargs: dict[str, Any]

    def get_queryset(self) -> Any:
        """Filter queryset to only include objects belonging to the current user."""
        queryset = super().get_queryset()  # type: ignore[misc]
        if not hasattr(self, "request") or self.request is None:
            return queryset.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        return queryset.filter(user=user)


class SetOwnerMixin:
    """
    Mixin that automatically sets the owner on create.
    """

    request: Any

    def perform_create(self, serializer: Any) -> None:
        """Set owner to current user before saving."""
        serializer.save(owner=self.request.user)


class SetUserMixin:
    """
    Mixin that automatically sets the user on create.
    """

    request: Any

    def perform_create(self, serializer: Any) -> None:
        """Set user to current user before saving."""
        serializer.save(user=self.request.user)
