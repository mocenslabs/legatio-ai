"""
Edge case tests for proposals.

Verifies behavior with extreme values, invalid states, and error conditions.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import PolicyDecision, Proposal
from apps.proposals.state_machine import VALID_TRANSITIONS
from core.enums import (
    AgentType,
    ConstitutionStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)
from core.exceptions import ProposalStateError

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


@pytest.fixture
def constitution_version(user, constitution):
    return ConstitutionVersion.objects.create(
        constitution=constitution,
        version_number=1,
        status=ConstitutionStatus.ACTIVE,
        created_by=user,
    )


@pytest.fixture
def room(user_agent, external_agent, constitution):
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-EDGE-010",
        title="Test",
        user_instruction="Test",
    )


@pytest.mark.django_db
class TestProposalEdgeCases:
    """Tests for Proposal edge cases."""

    def test_zero_amount(self, room, external_agent) -> None:
        """Proposal with zero amount."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("0.00"),
            currency="EUR",
            round_number=1,
        )
        assert proposal.amount == Decimal("0.00")

    def test_very_large_amount(self, room, external_agent) -> None:
        """Proposal with very large amount."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("9999999999.99"),
            currency="EUR",
            round_number=1,
        )
        assert proposal.amount == Decimal("9999999999.99")

    def test_negative_amount(self, room, external_agent) -> None:
        """Proposal with negative amount (edge case, should be allowed by model)."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("-100.00"),
            currency="EUR",
            round_number=1,
        )
        # Model allows negative amounts, but Policy Engine should handle this
        assert proposal.amount == Decimal("-100.00")

    def test_empty_data_fields(self, room, external_agent) -> None:
        """Proposal with empty data_fields_requested."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            data_fields_requested=[],
            round_number=1,
        )
        assert proposal.data_fields_requested == []

    def test_many_data_fields(self, room, external_agent) -> None:
        """Proposal with many data fields."""
        fields = [f"field_{i}" for i in range(100)]
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            data_fields_requested=fields,
            round_number=1,
        )
        assert len(proposal.data_fields_requested) == 100

    def test_invalid_transition_from_rejected(self, room, external_agent) -> None:
        """Cannot transition from REJECTED to any other state."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            status=ProposalStatus.REJECTED,
            round_number=1,
        )
        with pytest.raises(ProposalStateError):
            proposal.transition_to(ProposalStatus.RECEIVED)

    def test_invalid_transition_from_superseded(self, room, external_agent) -> None:
        """Cannot transition from SUPERSEDED to any other state."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            status=ProposalStatus.SUPERSEDED,
            round_number=1,
        )
        with pytest.raises(ProposalStateError):
            proposal.transition_to(ProposalStatus.RECEIVED)

    def test_invalid_transition_from_expired(self, room, external_agent) -> None:
        """Cannot transition from EXPIRED to any other state."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            status=ProposalStatus.EXPIRED,
            round_number=1,
        )
        with pytest.raises(ProposalStateError):
            proposal.transition_to(ProposalStatus.RECEIVED)

    def test_all_valid_transitions_defined(self) -> None:
        """All ProposalStatus values have transitions defined."""
        for status in ProposalStatus:
            assert status in VALID_TRANSITIONS

    def test_superseded_by_self(self, room, external_agent) -> None:
        """Proposal cannot be superseded by itself."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            round_number=1,
        )
        # This should be prevented at service layer, but model allows it
        proposal.superseded_by = proposal
        proposal.save()
        proposal.refresh_from_db()
        assert proposal.superseded_by == proposal


@pytest.mark.django_db
class TestPolicyDecisionEdgeCases:
    """Tests for PolicyDecision edge cases."""

    def test_zero_evaluation_duration(self, room, external_agent, constitution_version) -> None:
        """PolicyDecision with zero evaluation duration."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            round_number=1,
        )
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=0,
            engine_version="1.0.0",
        )
        assert decision.evaluation_duration_ms == 0

    def test_very_large_evaluation_duration(
        self, room, external_agent, constitution_version
    ) -> None:
        """PolicyDecision with very large evaluation duration."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            round_number=1,
        )
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=999999,
            engine_version="1.0.0",
        )
        assert decision.evaluation_duration_ms == 999999

    def test_empty_matched_rules(self, room, external_agent, constitution_version) -> None:
        """PolicyDecision with empty matched_rules."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            round_number=1,
        )
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            matched_rules=[],
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        assert decision.matched_rules == []

    def test_many_matched_rules(self, room, external_agent, constitution_version) -> None:
        """PolicyDecision with many matched rules."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            round_number=1,
        )
        rules = [
            {"rule_id": f"rule-{i}", "rule_number": i, "name": f"Rule {i}"} for i in range(100)
        ]
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            matched_rules=rules,
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        assert len(decision.matched_rules) == 100
