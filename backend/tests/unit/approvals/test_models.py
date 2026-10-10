"""
Unit tests for ApprovalRequest and ApprovalDecision models.
Source: 03-DATA-MODEL.md Section 11
"""

import uuid as uuid_module
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.agents.models import Agent
from apps.approvals.models import ApprovalDecision, ApprovalRequest
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    AgentType,
    ApprovalStatus,
    ConstitutionStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)
from core.exceptions import ApprovalStateError

User = get_user_model()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="user@example.com", password="pass")


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
        reference_code="NEG-2026-0001",
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
        terms={"nights": 5},
        status=ProposalStatus.RECEIVED,
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
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )


@pytest.mark.django_db
class TestApprovalRequestModel:
    def test_create_approval_request(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """ApprovalRequest can be created."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Amount €820 exceeds auto-approve limit of €200",
        )
        assert request.status == ApprovalStatus.PENDING
        assert request.expires_at is not None
        assert request.expires_at > timezone.now()

    def test_approval_request_id_is_uuid(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """ApprovalRequest ID is a UUID."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        assert isinstance(request.id, uuid_module.UUID)

    def test_approval_request_default_expires_at(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """ApprovalRequest has default expires_at of 24 hours."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        expected = timezone.now() + timedelta(hours=24)
        assert abs((request.expires_at - expected).total_seconds()) < 1

    def test_transition_to_approved(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """ApprovalRequest can transition to APPROVED."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        request.transition_to(ApprovalStatus.APPROVED)
        request.refresh_from_db()
        assert request.status == ApprovalStatus.APPROVED

    def test_transition_invalid_raises(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """Invalid transition raises ApprovalStateError."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        request.transition_to(ApprovalStatus.APPROVED)
        with pytest.raises(ApprovalStateError):
            request.transition_to(ApprovalStatus.PENDING)

    def test_is_expired(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """is_expired returns True if expires_at < now."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert request.is_expired is True

    def test_is_not_expired(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """is_expired returns False if expires_at > now."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        assert request.is_expired is False

    def test_proposal_fk_is_cascade(self) -> None:
        """ApprovalRequest.proposal FK has on_delete=CASCADE.

        Note: In practice, Proposal cannot be deleted while a PolicyDecision
        references it (PolicyDecision.proposal is PROTECT). This test verifies
        the FK definition at schema level.
        """
        from django.db import models

        field = ApprovalRequest._meta.get_field("proposal")
        assert field.remote_field.on_delete == models.CASCADE

    def test_proposal_delete_protected_by_policy_decision(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """Proposal cannot be deleted while PolicyDecision references it.

        PolicyDecision.proposal has on_delete=PROTECT, which prevents
        deletion of the Proposal. This is the expected behavior per
        03-DATA-MODEL.md Section 17.1 (referential integrity).
        """
        from django.db.models.deletion import ProtectedError

        ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        with pytest.raises(ProtectedError):
            proposal.delete()

    def test_str_representation(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """String representation includes status."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        assert "Pending" in str(request)


@pytest.mark.django_db
class TestApprovalDecisionModel:
    def test_create_decision(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
        user: Any,
    ) -> None:
        """ApprovalDecision can be created."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        decision = ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=ApprovalStatus.APPROVED,
            comment="Looks good",
        )
        assert decision.request == request
        assert decision.decided_by == user
        assert decision.decision == ApprovalStatus.APPROVED

    def test_decision_is_append_only(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
        user: Any,
    ) -> None:
        """ApprovalDecision cannot be updated."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        decision = ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=ApprovalStatus.APPROVED,
        )
        decision.decision = ApprovalStatus.REJECTED
        with pytest.raises(RuntimeError, match="append-only"):
            decision.save()

    def test_decision_cannot_be_deleted(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
        user: Any,
    ) -> None:
        """ApprovalDecision cannot be deleted."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        decision = ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=ApprovalStatus.APPROVED,
        )
        with pytest.raises(RuntimeError, match="append-only"):
            decision.delete()

    def test_decision_with_modifications(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
        user: Any,
    ) -> None:
        """ApprovalDecision can have modifications."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        decision = ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=ApprovalStatus.MODIFIED,
            modifications={"amount": 700},
            comment="Reduce amount to €700",
        )
        assert decision.decision == ApprovalStatus.MODIFIED
        assert decision.modifications == {"amount": 700}

    def test_system_decision_without_user(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
    ) -> None:
        """System decision (expired) can have decided_by=None."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        decision = ApprovalDecision.objects.create(
            request=request,
            decided_by=None,
            decision=ApprovalStatus.EXPIRED,
        )
        assert decision.decided_by is None
        assert decision.decision == ApprovalStatus.EXPIRED

    def test_cascade_delete_with_request(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
        user: Any,
    ) -> None:
        """Deleting request deletes decisions."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        decision = ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=ApprovalStatus.APPROVED,
        )
        decision_id = decision.id
        request.delete()
        assert not ApprovalDecision.objects.filter(id=decision_id).exists()

    def test_queryset_update_raises(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
        user: Any,
    ) -> None:
        """ApprovalDecision.objects.update() raises RuntimeError."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=ApprovalStatus.APPROVED,
        )
        with pytest.raises(RuntimeError, match="append-only"):
            ApprovalDecision.objects.all().update(comment="changed")

    def test_queryset_delete_raises(
        self,
        proposal: Any,
        room: Any,
        user_agent: Any,
        policy_decision: Any,
        user: Any,
    ) -> None:
        """ApprovalDecision.objects.delete() raises RuntimeError."""
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=user_agent,
            policy_decision=policy_decision,
            summary="Test",
        )
        ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=ApprovalStatus.APPROVED,
        )
        with pytest.raises(RuntimeError, match="append-only"):
            ApprovalDecision.objects.all().delete()
