"""
End-to-end test for Use Case 1: AI Travel Negotiation.

This test reproduces the complete flow from 04-BUSINESS-FLOW.md Section 4:
"Find me a hotel in Madrid for 5 nights. Don't spend more than EUR 700
and never share my phone number."

The test verifies:
- Round 1: EUR 820 -> REQUIRE_APPROVAL
- Round 2: EUR 680 + phone -> DENY
- Round 3: EUR 700, no phone -> REQUIRE_APPROVAL
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.audit.models import AuditEvent
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    AgentType,
    EventType,
    NegotiationStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
)
from services.negotiation_engine.orchestrator import NegotiationOrchestrator

User = get_user_model()


@pytest.fixture()
def user() -> Any:
    return User.objects.create_user(email="e2e@example.com", password="pass")


@pytest.fixture()
def user_agent(user: Any) -> Any:
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="My Travel Agent",
    )


@pytest.fixture()
def hotel_agent() -> Any:
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name="Hotel Agent",
    )


@pytest.fixture()
def madrid_constitution(user: Any, user_agent: Any) -> Any:
    """Constitution from 04-BUSINESS-FLOW.md Section 4.1."""
    rules = [
        {
            "rule_number": 1,
            "name": "Max transaction amount",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 700,
            "action": "ALLOW",
        },
        {
            "rule_number": 17,
            "name": "Never share phone number",
            "category": "PRIVACY",
            "field": "data_fields_requested",
            "operator": "CONTAINS",
            "value": "phone_number",
            "action": "DENY",
        },
        {
            "rule_number": 23,
            "name": "Large payments need approval",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 200,
            "action": "REQUIRE_APPROVAL",
        },
        {
            "rule_number": 31,
            "name": "Email sharing requires approval",
            "category": "PRIVACY",
            "field": "data_fields_requested",
            "operator": "CONTAINS",
            "value": "email",
            "action": "REQUIRE_APPROVAL",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent,
        name="Madrid Travel Rules",
        description="Rules for hotel booking in Madrid",
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.mark.django_db()
class TestUseCase1TravelNegotiation:
    """Full scenario from 04-BUSINESS-FLOW.md Section 4.2."""

    def test_full_negotiation_flow(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        madrid_constitution: Any,
    ) -> None:
        """
        Complete flow:
        Round 1: EUR 820, no phone -> REQUIRE_APPROVAL
        Round 2: EUR 680, with phone -> DENY
        Round 3: EUR 700, no phone -> REQUIRE_APPROVAL
        """
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=madrid_constitution,
            title="Hotel Madrid 5 nights",
            user_instruction="Find hotel in Madrid for 5 nights. Max EUR 700. Never share phone.",
            max_rounds=10,
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()

        # Round 1: EUR 820, no phone
        result1 = orchestrator.process_round()
        assert result1["proposal"].amount == 820
        assert result1["proposal"].data_fields_requested == []
        assert result1["outcome"] == "REQUIRE_HUMAN_APPROVAL"
        assert result1["proposal"].status == ProposalStatus.PENDING_APPROVAL

        # Round 2: EUR 680, with phone -> DENY
        result2 = orchestrator.process_round()
        assert result2["proposal"].amount == 680
        assert "phone_number" in result2["proposal"].data_fields_requested
        assert result2["outcome"] == "DENY"
        assert result2["proposal"].status == ProposalStatus.DENIED
        assert result2["counter_offer"] is not None

        # Round 3: EUR 700, no phone -> REQUIRE_APPROVAL
        result3 = orchestrator.process_round()
        assert result3["proposal"].amount == 700
        assert result3["proposal"].data_fields_requested == []
        assert result3["outcome"] == "REQUIRE_HUMAN_APPROVAL"
        assert result3["proposal"].status == ProposalStatus.PENDING_APPROVAL

        room.refresh_from_db()
        assert room.status == NegotiationStatus.AWAITING_APPROVAL

    def test_audit_trail_completeness(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        madrid_constitution: Any,
    ) -> None:
        """Verify that the audit trail contains all expected events."""
        initial_count = AuditEvent.objects.count()
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=madrid_constitution,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()
        orchestrator.process_round()
        orchestrator.process_round()

        events = AuditEvent.objects.all().order_by("created_at")
        assert events.count() >= initial_count + 9

        event_types = [e.event_type for e in events]
        assert EventType.NEGOTIATION_STARTED in event_types
        assert EventType.PROPOSAL_RECEIVED in event_types
        assert EventType.PROPOSAL_EVALUATED in event_types
        assert EventType.PROPOSAL_DENIED in event_types
        assert EventType.COUNTERPROPOSAL_CREATED in event_types

    def test_policy_decisions_created(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        madrid_constitution: Any,
    ) -> None:
        """Verify that PolicyDecision records are created for each proposal."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=madrid_constitution,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()
        orchestrator.process_round()
        orchestrator.process_round()

        decisions = PolicyDecision.objects.filter(proposal__room=room)
        assert decisions.count() == 3

        outcomes = [d.outcome for d in decisions]
        assert PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL in outcomes
        assert PolicyDecisionOutcome.DENY in outcomes

    def test_proposals_created(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        madrid_constitution: Any,
    ) -> None:
        """Verify that Proposal records are created for each round."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=madrid_constitution,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()
        orchestrator.process_round()
        orchestrator.process_round()

        proposals = Proposal.objects.filter(room=room)
        assert proposals.count() == 3

        amounts = [p.amount for p in proposals]
        assert 820 in amounts
        assert 680 in amounts
        assert 700 in amounts
