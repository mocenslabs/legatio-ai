"""
Tests to cover managers.py methods in negotiations and proposals apps.
Targets: managers.py lines 17, 20-25, 35, 42, 45
Source: DEL-026
"""

from typing import Any, cast

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from apps.negotiations.managers import NegotiationSoftDeleteQuerySet
from apps.negotiations.models import NegotiationMessage, NegotiationRoom
from core.enums import ActorType, AgentType, NegotiationMessageType

User = get_user_model()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="manager@example.com", password="pass")


@pytest.fixture
def user_agent(user: Any) -> Any:
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent() -> Any:
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="External Agent")


@pytest.fixture
def constitution(user: Any, user_agent: Any) -> Any:
    return Constitution.objects.create(
        agent=user_agent,
        name="Test Constitution",
        status="ACTIVE",
    )


@pytest.mark.django_db
class TestNegotiationManagerCoverage:
    """Cover managers.py in negotiations app."""

    def test_default_queryset_excludes_deleted(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """NegotiationSoftDeleteManager.get_queryset() calls alive() internally."""
        room1 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-001",
            title="Test 1",
            user_instruction="test",
        )
        room2 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-002",
            title="Test 2",
            user_instruction="test",
        )

        # Soft delete room2
        room2.soft_delete()

        # Default manager excludes deleted (get_queryset calls alive())
        assert NegotiationRoom.objects.filter(id=room1.id).exists()
        assert not NegotiationRoom.objects.filter(id=room2.id).exists()

    def test_all_with_deleted_includes_soft_deleted(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """all_with_deleted() returns all rooms including soft-deleted."""
        room1 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-003",
            title="Test 1",
            user_instruction="test",
        )
        room2 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-004",
            title="Test 2",
            user_instruction="test",
        )
        room2.soft_delete()

        # all_with_deleted includes both
        all_rooms = NegotiationRoom.objects.all_with_deleted()
        assert all_rooms.filter(id=room1.id).exists()
        assert all_rooms.filter(id=room2.id).exists()

    def test_alive_queryset_method(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """Line 17: alive() on queryset returns only non-deleted rooms."""
        room1 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-005",
            title="Test 1",
            user_instruction="test",
        )
        room2 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-006",
            title="Test 2",
            user_instruction="test",
        )
        room2.soft_delete()

        # alive() is a queryset method, accessed via .all().alive()
        alive_rooms = NegotiationRoom.objects.all_with_deleted().alive()
        assert alive_rooms.filter(id=room1.id).exists()
        assert not alive_rooms.filter(id=room2.id).exists()

    def test_dead_queryset_method(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """Line 20: dead() on queryset returns only soft-deleted rooms."""
        room1 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-007",
            title="Test 1",
            user_instruction="test",
        )
        room2 = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-008",
            title="Test 2",
            user_instruction="test",
        )
        room2.soft_delete()

        # dead() is a queryset method
        dead_rooms = NegotiationRoom.objects.all_with_deleted().dead()
        assert not dead_rooms.filter(id=room1.id).exists()
        assert dead_rooms.filter(id=room2.id).exists()

    def test_soft_delete_queryset_returns_count(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """Lines 24-25: soft delete() returns count and details dict."""
        NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-009",
            title="Test",
            user_instruction="test",
        )

        queryset = cast(
            NegotiationSoftDeleteQuerySet,
            NegotiationRoom.objects.filter(reference_code="NEG-MAN-009"),
        )
        count, details = queryset.delete(hard=False)

        assert count == 1
        assert "negotiations.NegotiationRoom" in details

    def test_hard_delete_queryset_removes_from_db(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """hard=True removes records from database entirely."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-010",
            title="Test",
            user_instruction="test",
        )
        room_id = room.id

        queryset = cast(NegotiationSoftDeleteQuerySet, NegotiationRoom.objects.filter(id=room_id))
        queryset.delete(hard=True)

        # Not in all_with_deleted either (hard delete)
        assert not (NegotiationRoom.objects.all_with_deleted().filter(id=room_id).exists())


@pytest.mark.django_db
class TestAppendOnlyManagerCoverage:
    """Cover AppendOnlyQuerySet in managers.py."""

    def test_append_only_update_raises(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """Line 42: AppendOnlyQuerySet.update() raises RuntimeError."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-011",
            title="Test",
            user_instruction="test",
        )
        NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.SYSTEM,
            sender_id=None,
            message_type=NegotiationMessageType.PROPOSAL,
            content="Test",
            round_number=1,
        )

        with pytest.raises(RuntimeError, match="append-only"):
            NegotiationMessage.objects.all().update(content="Updated")

    def test_append_only_delete_raises(
        self,
        user_agent: Any,
        external_agent: Any,
        constitution: Any,
    ) -> None:
        """Line 45: AppendOnlyQuerySet.delete() raises RuntimeError."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-MAN-012",
            title="Test",
            user_instruction="test",
        )
        NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.SYSTEM,
            sender_id=None,
            message_type=NegotiationMessageType.PROPOSAL,
            content="Test",
            round_number=1,
        )

        with pytest.raises(RuntimeError, match="append-only"):
            NegotiationMessage.objects.all().delete()
