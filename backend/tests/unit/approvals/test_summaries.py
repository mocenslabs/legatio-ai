"""
Unit tests for approval summaries.
Source: 04-BUSINESS-FLOW.md Section 9.2
"""

from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.approvals.summaries import (
    generate_approval_summary,
    generate_rejection_summary,
)
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    AgentType,
    ConstitutionStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)

User = get_user_model()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="summary@example.com", password="pass")


@pytest.fixture
def user_agent(user: Any) -> Any:
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent() -> Any:
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="Hotel Agent")


@pytest.fixture
def constitution(user: Any, user_agent: Any) -> Any:
    return Constitution.objects.create(
        agent=user_agent, name="Travel", status=ConstitutionStatus.ACTIVE
    )


@pytest.fixture
def constitution_version(user: Any, constitution: Any) -> Any:
    return ConstitutionVersion.objects.create(
        constitution=constitution, version_number=1, created_by=user
    )


@pytest.fixture
def room(user_agent: Any, external_agent: Any, constitution: Any) -> Any:
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-SUMMARY-001",
        title="Test",
        user_instruction="Test",
    )


@pytest.fixture
def proposal(room: Any, external_agent: Any) -> Any:
    return Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("820.00"),
        currency="EUR",
        data_fields_requested=[],
        terms={"nights": 5, "destination": "Madrid"},
        status=ProposalStatus.EVALUATING,
        round_number=1,
    )


@pytest.fixture
def policy_decision(proposal: Any, constitution_version: Any) -> Any:
    return PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=constitution_version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.LOW,
        reason="Amount exceeds auto-approve limit",
        matched_rules=[
            {
                "rule_id": "rule-23",
                "rule_number": 23,
                "name": "Large payments",
                "action": "REQUIRE_APPROVAL",
            }
        ],
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )


@pytest.mark.django_db
class TestGenerateApprovalSummary:
    def test_purchase_summary(self, proposal: Any, policy_decision: Any) -> None:
        """Purchase proposal generates readable summary."""
        summary = generate_approval_summary(proposal, policy_decision)
        assert "Approval Required" in summary
        assert "820.00" in summary
        assert "Madrid" in summary
        assert "5 nights" in summary
        assert "Risk level" in summary

    def test_summary_includes_reason(self, proposal: Any, policy_decision: Any) -> None:
        """Summary includes the policy decision reason."""
        summary = generate_approval_summary(proposal, policy_decision)
        assert "exceeds auto-approve limit" in summary

    def test_summary_includes_matched_rules(self, proposal: Any, policy_decision: Any) -> None:
        """Summary includes matched rules."""
        summary = generate_approval_summary(proposal, policy_decision)
        assert "Rule #23" in summary
        assert "Large payments" in summary

    def test_summary_no_data_fields(self, proposal: Any, policy_decision: Any) -> None:
        """Summary shows 'None' when no data fields requested."""
        summary = generate_approval_summary(proposal, policy_decision)
        assert "Data requested: None" in summary


@pytest.mark.django_db
class TestGenerateRejectionSummary:
    def test_rejection_summary(self, proposal: Any, policy_decision: Any) -> None:
        """Rejection generates readable summary."""
        summary = generate_rejection_summary(proposal, policy_decision)
        assert "Rejected" in summary
        assert "820.00" in summary
