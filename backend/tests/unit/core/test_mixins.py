"""
Unit tests for core mixins.

Verifies that ownership filtering works correctly.

Note: ``OwnedQuerySetMixin`` filters by ``owner``, but no concrete model with
an ``owner`` FK exists yet (Agent arrives in a later phase; ``UserProfile``
uses ``user``). To keep these tests pure unit tests of the mixin logic, we
test it against a lightweight queryset double that records filter calls.
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from apps.accounts.models import UserProfile
from core.mixins import OwnedQuerySetMixin, UserScopedQuerySetMixin

User = get_user_model()


class FakeQuerySet:
    """Minimal QuerySet double that records filters instead of hitting the DB."""

    def __init__(self, items: list[Any] | None = None) -> None:
        self.items: list[Any] = list(items) if items is not None else []
        self.none_called: bool = False
        self.filter_calls: list[dict[str, Any]] = []

    def none(self) -> "FakeQuerySet":
        empty = FakeQuerySet(items=[])
        empty.none_called = True
        return empty

    def filter(self, **kwargs: Any) -> "FakeQuerySet":
        filtered = FakeQuerySet(items=self.items)
        filtered.filter_calls = [*self.filter_calls, kwargs]
        return filtered


class BaseFakeViewSet:
    """
    Stand-in for ``GenericAPIView``.

    Owns ``request`` and the raw queryset. The queryset is typed ``Any``
    because tests intentionally pass either ``FakeQuerySet`` (for
    ``owner``-based mixins, where no concrete model exists yet) or a real
    Django ``QuerySet`` (for ``user``-based mixins against ``UserProfile``).

    Mixins must be listed BEFORE this class in ``bases`` so their
    ``super().get_queryset()`` resolves here.
    """

    def __init__(self, request: Any, queryset: Any) -> None:
        self.request = request
        self._queryset = queryset

    def get_queryset(self) -> Any:
        return self._queryset


class FakeOwnedViewSet(OwnedQuerySetMixin, BaseFakeViewSet):
    """Mimics: class MyViewSet(OwnedQuerySetMixin, ModelViewSet)."""


class FakeUserScopedViewSet(UserScopedQuerySetMixin, BaseFakeViewSet):
    """Mimics: class MyViewSet(UserScopedQuerySetMixin, ModelViewSet)."""


def _request_with_user(user: Any) -> Any:
    """Build a factory request with ``user`` attached (None allowed)."""
    request: Any = APIRequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestOwnedQuerySetMixin:
    def test_filters_by_owner(self) -> None:
        """Authenticated user -> queryset filtered with ``owner=user``."""
        user = User.objects.create_user(
            email="owner@example.com",
            password="pass1234!",
        )
        view = FakeOwnedViewSet(
            _request_with_user(user),
            FakeQuerySet(items=[object(), object()]),
        )

        result = view.get_queryset()

        assert result.filter_calls == [{"owner": user}]

    def test_returns_empty_for_anonymous(self) -> None:
        """Anonymous user -> ``queryset.none()``."""
        view = FakeOwnedViewSet(
            _request_with_user(AnonymousUser()),
            FakeQuerySet(items=[object()]),
        )

        result = view.get_queryset()

        assert result.none_called is True
        assert result.items == []

    def test_returns_empty_for_none_user(self) -> None:
        """``user=None`` -> ``queryset.none()``."""
        view = FakeOwnedViewSet(
            _request_with_user(None),
            FakeQuerySet(items=[object()]),
        )

        result = view.get_queryset()

        assert result.none_called is True
        assert result.items == []


@pytest.mark.django_db
class TestUserScopedQuerySetMixin:
    def test_filters_by_user(self) -> None:
        """Authenticated user -> only rows whose ``user`` FK matches."""
        user1 = User.objects.create_user(
            email="scoped1@example.com",
            password="pass1234!",
        )
        user2 = User.objects.create_user(
            email="scoped2@example.com",
            password="pass1234!",
        )
        UserProfile.objects.create(user=user1, display_name="User 1")
        UserProfile.objects.create(user=user2, display_name="User 2")

        view = FakeUserScopedViewSet(
            _request_with_user(user2),
            UserProfile.objects.all(),
        )

        profiles = list(view.get_queryset())

        assert len(profiles) == 1
        assert profiles[0].user == user2

    def test_returns_empty_for_anonymous(self) -> None:
        """Anonymous user -> empty queryset."""
        user = User.objects.create_user(
            email="scoped-anon@example.com",
            password="pass1234!",
        )
        UserProfile.objects.create(user=user, display_name="Anon target")

        view = FakeUserScopedViewSet(
            _request_with_user(AnonymousUser()),
            UserProfile.objects.all(),
        )

        assert view.get_queryset().count() == 0

    def test_returns_empty_for_none_user(self) -> None:
        """``user=None`` -> empty queryset."""
        user = User.objects.create_user(
            email="scoped-none@example.com",
            password="pass1234!",
        )
        UserProfile.objects.create(user=user, display_name="None target")

        view = FakeUserScopedViewSet(
            _request_with_user(None),
            UserProfile.objects.all(),
        )

        assert view.get_queryset().count() == 0
