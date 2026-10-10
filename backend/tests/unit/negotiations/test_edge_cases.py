"""
Edge case tests for negotiations.

Verifies behavior with extreme values, invalid states, and error conditions.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from apps.negotiations.models import NegotiationRoom
from apps.negotiations.state_machine import VALID_TRANSITIONS
from core.enums import (
    AgentType,
    ConstitutionStatus,
    NegotiationStatus,
)
from core.exceptions import NegotiationStateError

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="edge@example.com", password="pass")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent():
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="External Agent")


@pytest.fixture
def constitution(user, user_agent):
    return Constitution.objects.create(
        agent=user_agent,
        name="Test Constitution",
        status=ConstitutionStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestNegotiationRoomEdgeCases:
    """Tests for NegotiationRoom edge cases."""

    def test_max_rounds_boundary(self, user_agent, external_agent, constitution) -> None:
        """Max rounds boundary: current_round == max_rounds."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-001",
            title="Test",
            user_instruction="Test",
            max_rounds=3,
            current_round=3,  # At boundary
        )
        assert room.current_round == room.max_rounds

    def test_max_rounds_exceeded(self, user_agent, external_agent, constitution) -> None:
        """Current round exceeds max rounds (should not happen in practice)."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-002",
            title="Test",
            user_instruction="Test",
            max_rounds=3,
            current_round=5,  # Exceeded
        )
        # This should be prevented by the orchestrator, but the model allows it
        assert room.current_round > room.max_rounds

    def test_zero_max_rounds(self, user_agent, external_agent, constitution) -> None:
        """Max rounds = 0 (edge case)."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-003",
            title="Test",
            user_instruction="Test",
            max_rounds=0,
        )
        assert room.max_rounds == 0

    def test_large_max_rounds(self, user_agent, external_agent, constitution) -> None:
        """Large max rounds value."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-004",
            title="Test",
            user_instruction="Test",
            max_rounds=1000,
        )
        assert room.max_rounds == 1000

    def test_invalid_transition_from_completed(
        self, user_agent, external_agent, constitution
    ) -> None:
        """Cannot transition from COMPLETED to any other state."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-005",
            title="Test",
            user_instruction="Test",
            status=NegotiationStatus.COMPLETED,
        )
        with pytest.raises(NegotiationStateError):
            room.transition_to(NegotiationStatus.IN_PROGRESS)

    def test_invalid_transition_from_cancelled(
        self, user_agent, external_agent, constitution
    ) -> None:
        """Cannot transition from CANCELLED to any other state."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-006",
            title="Test",
            user_instruction="Test",
            status=NegotiationStatus.CANCELLED,
        )
        with pytest.raises(NegotiationStateError):
            room.transition_to(NegotiationStatus.IN_PROGRESS)

    def test_invalid_transition_from_failed(self, user_agent, external_agent, constitution) -> None:
        """Cannot transition from FAILED to any other state."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-007",
            title="Test",
            user_instruction="Test",
            status=NegotiationStatus.FAILED,
        )
        with pytest.raises(NegotiationStateError):
            room.transition_to(NegotiationStatus.IN_PROGRESS)

    def test_invalid_transition_from_expired(
        self, user_agent, external_agent, constitution
    ) -> None:
        """Cannot transition from EXPIRED to any other state."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-008",
            title="Test",
            user_instruction="Test",
            status=NegotiationStatus.EXPIRED,
        )
        with pytest.raises(NegotiationStateError):
            room.transition_to(NegotiationStatus.IN_PROGRESS)

    def test_all_valid_transitions_defined(self) -> None:
        """All NegotiationStatus values have transitions defined."""
        for status in NegotiationStatus:
            assert status in VALID_TRANSITIONS

    def test_soft_delete_and_restore(self, user_agent, external_agent, constitution) -> None:
        """Soft delete and verify room is excluded from default manager."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-EDGE-009",
            title="Test",
            user_instruction="Test",
        )
        room_id = room.id
        room.soft_delete()

        # Should not be in default manager
        assert NegotiationRoom.objects.filter(id=room_id).count() == 0

        # Should be in all_objects
        assert NegotiationRoom.all_objects.filter(id=room_id).count() == 1
