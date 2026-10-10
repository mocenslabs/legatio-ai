"""
Integration tests for the complete approval flow.
Verifies the integration between negotiation orchestrator and approval services.
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.approvals.models import ApprovalRequest
from apps.approvals.services import process_approval_decision
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.proposals.models import Proposal
from core.enums import (
    AgentType,
    ApprovalStatus,
    NegotiationStatus,
    ProposalStatus,
)
from services.negotiation_engine.orchestrator import NegotiationOrchestrator

User = get_user_model()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture
def user_agent(user: Any) -> Any:
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def hotel_agent() -> Any:
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="Hotel Agent")


@pytest.fixture
def constitution_with_rules(user: Any, user_agent: Any) -> Any:
    rules = [
        {
            "rule_number": 1,
            "name": "Max transaction",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 700,
            "action": "ALLOW",
        },
        {
            "rule_number": 23,
            "name": "Large payments",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 200,
            "action": "REQUIRE_APPROVAL",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent,
        name="Travel Rules",
        description=None,
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.mark.django_db
class TestApprovalFlowIntegration:
    def test_orchestrator_creates_approval_request(
        self, user: Any, user_agent: Any, hotel_agent: Any, constitution_with_rules: Any
    ) -> None:
        """Orchestrator creates ApprovalRequest when REQUIRE_HUMAN_APPROVAL."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()

        # Process round (should create ApprovalRequest)
        result = orchestrator.process_round()
        assert result["outcome"] == "REQUIRE_HUMAN_APPROVAL"

        # Check that ApprovalRequest was created
        assert ApprovalRequest.objects.filter(room=room).exists()
        request = ApprovalRequest.objects.get(room=room)
        assert request.status == ApprovalStatus.PENDING
        assert "Approval Required" in request.summary

    def test_full_approval_flow(
        self, user: Any, user_agent: Any, hotel_agent: Any, constitution_with_rules: Any
    ) -> None:
        """Full flow: negotiation -> approval -> decision."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()

        # Process round
        result = orchestrator.process_round()
        assert result["outcome"] == "REQUIRE_HUMAN_APPROVAL"

        # Get approval request
        request = ApprovalRequest.objects.get(room=room)

        # User approves
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.APPROVED,
            comment="Approved",
        )
        assert decision.decision == ApprovalStatus.APPROVED

        request.refresh_from_db()
        assert request.status == ApprovalStatus.APPROVED

        # Check proposal status
        proposal = Proposal.objects.get(room=room)
        assert proposal.status == ProposalStatus.ACCEPTED

        # Check room status
        room.refresh_from_db()
        assert room.status == NegotiationStatus.AWAITING_APPROVAL
