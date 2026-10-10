"""
Unit tests for NegotiationRoom and NegotiationMessage models.
Source: 03-DATA-MODEL.md Sections 9 and 10
"""

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from apps.negotiations.models import NegotiationMessage, NegotiationRoom
from core.enums import (
    ActorType,
    AgentType,
    ConstitutionStatus,
    NegotiationMessageType,
    NegotiationStatus,
)
from core.exceptions import NegotiationStateError

User = get_user_model()


@pytest.fixture
def user() -> User:  # type: ignore[valid-type]
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture
def user_agent(user: User) -> Agent:  # type: ignore[valid-type]
    return Agent.objects.create(  # type: ignore[no-any-return]
        owner=user, agent_type=AgentType.USER_AGENT, name="User Agent"
    )


@pytest.fixture
def external_agent() -> Agent:
    return Agent.objects.create(  # type: ignore[no-any-return]
        owner=None, agent_type=AgentType.EXTERNAL_AGENT, name="Hotel Agent"
    )


@pytest.fixture
def constitution(user: User, user_agent: Agent) -> Constitution:  # type: ignore[valid-type]
    return Constitution.objects.create(  # type: ignore[no-any-return]
        agent=user_agent, name="Travel", status=ConstitutionStatus.ACTIVE
    )


@pytest.fixture
def room(user_agent: Agent, external_agent: Agent, constitution: Constitution) -> NegotiationRoom:
    return NegotiationRoom.objects.create(  # type: ignore[no-any-return]
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-2026-0001",
    )


@pytest.mark.django_db
class TestNegotiationRoom:
    def test_create_room(self, room: NegotiationRoom) -> None:
        assert room.status == NegotiationStatus.PENDING
        assert room.current_round == 0
        assert room.max_rounds == 10
        assert room.is_active is True
        assert room.is_terminal is False

    def test_transition_to_in_progress(self, room: NegotiationRoom) -> None:
        room.transition_to(NegotiationStatus.IN_PROGRESS)
        room.refresh_from_db()
        assert room.status == NegotiationStatus.IN_PROGRESS
        assert room.started_at is not None

    def test_transition_invalid_raises(self, room: NegotiationRoom) -> None:
        with pytest.raises(NegotiationStateError):
            room.transition_to(NegotiationStatus.COMPLETED)

    def test_increment_round(self, room: NegotiationRoom) -> None:
        room.increment_round()
        assert room.current_round == 1
        room.increment_round()
        assert room.current_round == 2

    def test_terminal_state(self, room: NegotiationRoom) -> None:
        room.transition_to(NegotiationStatus.IN_PROGRESS)
        room.transition_to(NegotiationStatus.FAILED)
        room.refresh_from_db()
        assert room.is_terminal is True
        assert room.is_active is False

    def test_cancel_from_pending(self, room: NegotiationRoom) -> None:
        room.transition_to(NegotiationStatus.CANCELLED)
        room.refresh_from_db()
        assert room.status == NegotiationStatus.CANCELLED
        assert room.cancelled_at is not None

    def test_soft_delete(self, room: NegotiationRoom) -> None:
        room.soft_delete()
        assert NegotiationRoom.objects.count() == 0
        assert NegotiationRoom.all_objects.count() == 1

    def test_str_representation(self, room: NegotiationRoom) -> None:
        assert "NEG-2026-0001" in str(room)


@pytest.mark.django_db
class TestNegotiationMessage:
    def test_create_message(self, room: NegotiationRoom) -> None:
        msg = NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.EXTERNAL_AGENT,
            sender_id=room.external_agent.id,
            message_type=NegotiationMessageType.TEXT,
            content={"text": "I offer €820 for 5 nights"},
            round_number=1,
        )
        assert msg.room == room
        assert msg.round_number == 1

    def test_message_is_append_only(self, room: NegotiationRoom) -> None:
        msg = NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.SYSTEM,
            message_type=NegotiationMessageType.SYSTEM,
            content={"text": "Negotiation started"},
            round_number=0,
        )
        msg.content = {"text": "modified"}
        with pytest.raises(RuntimeError, match="append-only"):
            msg.save()

    def test_message_cannot_be_deleted(self, room: NegotiationRoom) -> None:
        msg = NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.SYSTEM,
            message_type=NegotiationMessageType.SYSTEM,
            content={"text": "test"},
            round_number=0,
        )
        with pytest.raises(RuntimeError, match="append-only"):
            msg.delete()

    def test_cascade_delete_with_room(self, room: NegotiationRoom) -> None:
        NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.SYSTEM,
            message_type=NegotiationMessageType.SYSTEM,
            content={"text": "test"},
            round_number=0,
        )
        room_id = room.id
        room.delete()
        assert NegotiationMessage.objects.filter(room_id=room_id).count() == 0
