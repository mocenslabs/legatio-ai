"""
Unit tests for Proposal, CounterProposal, and PolicyDecision models.
Source: 03-DATA-MODEL.md Section 10
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import CounterProposal, PolicyDecision, Proposal
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
def constitution_version(user: User, constitution: Constitution) -> ConstitutionVersion:  # type: ignore[valid-type]
    return ConstitutionVersion.objects.create(  # type: ignore[no-any-return]
        constitution=constitution, version_number=1, created_by=user
    )


@pytest.fixture
def room(user_agent: Agent, external_agent: Agent, constitution: Constitution) -> NegotiationRoom:
    return NegotiationRoom.objects.create(  # type: ignore[no-any-return]
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-2026-0001",
    )


@pytest.fixture
def proposal(room: NegotiationRoom, external_agent: Agent) -> Proposal:
    return Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("820.00"),
        currency="EUR",
        data_fields_requested=[],
        terms={"nights": 5, "breakfast": True},
        round_number=1,
    )


@pytest.mark.django_db
class TestProposalModel:
    def test_create_proposal(self, proposal: Proposal) -> None:
        assert proposal.status == ProposalStatus.RECEIVED
        assert proposal.amount == Decimal("820.00")
        assert proposal.currency == "EUR"
        assert proposal.round_number == 1

    def test_transition_to_evaluating(self, proposal: Proposal) -> None:
        proposal.transition_to(ProposalStatus.EVALUATING)
        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.EVALUATING

    def test_transition_invalid_raises(self, proposal: Proposal) -> None:
        with pytest.raises(ProposalStateError):
            proposal.transition_to(ProposalStatus.ACCEPTED)

    def test_terminal_state(self, proposal: Proposal) -> None:
        proposal.transition_to(ProposalStatus.EVALUATING)
        proposal.transition_to(ProposalStatus.DENIED)
        proposal.transition_to(ProposalStatus.SUPERSEDED)
        proposal.refresh_from_db()
        assert proposal.is_terminal is True

    def test_has_policy_decision_false_initially(self, proposal: Proposal) -> None:
        assert proposal.has_policy_decision is False

    def test_has_policy_decision_true_after_creation(
        self, proposal: Proposal, constitution_version: ConstitutionVersion
    ) -> None:
        PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="All checks passed",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        assert proposal.has_policy_decision is True

    def test_cascade_delete_with_room(self, room: NegotiationRoom, proposal: Proposal) -> None:
        proposal_id = proposal.id
        room.delete()
        assert not Proposal.objects.filter(id=proposal_id).exists()

    def test_superseded_by(self, proposal: Proposal, external_agent: Agent) -> None:
        new_proposal = Proposal.objects.create(
            room=proposal.room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("700.00"),
            currency="EUR",
            round_number=2,
        )
        proposal.superseded_by = new_proposal
        proposal.save()
        proposal.refresh_from_db()
        assert proposal.superseded_by == new_proposal

    def test_str_representation(self, proposal: Proposal) -> None:
        assert "€820" in str(proposal)
        assert "Received" in str(proposal)


@pytest.mark.django_db
class TestCounterProposalModel:
    def test_create_counter_proposal(self, proposal: Proposal, external_agent: Agent) -> None:
        counter = CounterProposal.objects.create(
            proposal=proposal,
            sender=external_agent,
            adjustments={"amount": 680, "remove_phone": True},
            reasoning="We can do €680 without phone number",
        )
        assert counter.proposal == proposal
        assert counter.adjustments["amount"] == 680

    def test_counter_proposal_is_append_only(
        self, proposal: Proposal, external_agent: Agent
    ) -> None:
        counter = CounterProposal.objects.create(
            proposal=proposal,
            sender=external_agent,
            adjustments={"amount": 680},
        )
        counter.adjustments = {"amount": 700}
        with pytest.raises(RuntimeError, match="append-only"):
            counter.save()

    def test_counter_proposal_cannot_be_deleted(
        self, proposal: Proposal, external_agent: Agent
    ) -> None:
        counter = CounterProposal.objects.create(
            proposal=proposal,
            sender=external_agent,
            adjustments={"amount": 680},
        )
        with pytest.raises(RuntimeError, match="append-only"):
            counter.delete()

    def test_cascade_delete_with_proposal(self, proposal: Proposal, external_agent: Agent) -> None:
        counter = CounterProposal.objects.create(
            proposal=proposal,
            sender=external_agent,
            adjustments={"amount": 680},
        )
        counter_id = counter.id
        proposal.delete()
        assert not CounterProposal.objects.filter(id=counter_id).exists()


@pytest.mark.django_db
class TestPolicyDecisionModel:
    def test_create_policy_decision(
        self, proposal: Proposal, constitution_version: ConstitutionVersion
    ) -> None:
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="All checks passed",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        assert decision.proposal == proposal
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_policy_decision_is_append_only(
        self, proposal: Proposal, constitution_version: ConstitutionVersion
    ) -> None:
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        decision.outcome = PolicyDecisionOutcome.DENY
        with pytest.raises(RuntimeError, match="append-only"):
            decision.save()

    def test_policy_decision_cannot_be_deleted(
        self, proposal: Proposal, constitution_version: ConstitutionVersion
    ) -> None:
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        with pytest.raises(RuntimeError, match="append-only"):
            decision.delete()

    def test_matched_rules_stored_as_json(
        self, proposal: Proposal, constitution_version: ConstitutionVersion
    ) -> None:
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.CRITICAL,
            reason="Blocked by Rule #17",
            matched_rules=[
                {
                    "rule_id": "rule-17",
                    "rule_number": 17,
                    "name": "Never share phone",
                    "action": "DENY",
                    "triggered_by": "data_fields_requested contains 'phone_number'",
                }
            ],
            evaluation_duration_ms=12,
            engine_version="1.0.0",
        )
        assert len(decision.matched_rules) == 1
        assert decision.matched_rules[0]["rule_number"] == 17

    def test_cascade_delete_with_proposal(
        self, proposal: Proposal, constitution_version: ConstitutionVersion
    ) -> None:
        decision = PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        decision_id = decision.id
        proposal.delete()
        assert not PolicyDecision.objects.filter(id=decision_id).exists()

    def test_constitution_version_protected(
        self, proposal: Proposal, constitution_version: ConstitutionVersion
    ) -> None:
        """Deleting constitution_version should be blocked by PROTECT."""
        PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        from django.db.models import ProtectedError

        with pytest.raises(ProtectedError):
            constitution_version.delete()
