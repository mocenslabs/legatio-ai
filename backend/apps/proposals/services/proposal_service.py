"""Proposal Service layer.

This module orchestrates the proposal lifecycle: creation, policy evaluation,
approval request generation, and final execution. It integrates the pure
Policy Engine with the Proposal and ApprovalRequest models.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction

from apps.approvals.models import ApprovalRequest, ApprovalStatus
from apps.policies.engine.types import DecisionOutcome
from apps.policies.services import PolicyEngineService
from apps.proposals.models import Proposal, ProposalStatus


class ProposalServiceError(Exception):
    """Base exception for proposal service errors."""


class InvalidTransitionError(ProposalServiceError):
    """Raised when a proposal state transition is not allowed."""


class ProposalService:
    """Service layer for proposal lifecycle operations.

    Orchestrates the full proposal workflow:
    1. Create proposal (DRAFT)
    2. Submit for policy evaluation
    3. Route based on decision (ALLOW/DENY/REQUIRE_HUMAN_APPROVAL)
    4. Generate approval requests when needed
    5. Resolve approvals and finalize status
    6. Execute approved proposals
    """

    @staticmethod
    @transaction.atomic
    def create_proposal(
        title: str,
        action_type: str,
        target_resource: str,
        payload: dict[str, Any],
        created_by_id: uuid.UUID,
        description: str = "",
        constitution_id: uuid.UUID | None = None,
    ) -> Proposal:
        """Create a new proposal in DRAFT status.

        Args:
            title: Human-readable title for the proposal.
            action_type: The type of action being proposed.
            target_resource: The resource the action targets.
            payload: JSON data associated with the action.
            created_by_id: UUID of the user creating the proposal.
            description: Optional detailed description.
            constitution_id: Optional UUID of the constitution to scope evaluation.

        Returns:
            The created Proposal instance.
        """
        return Proposal.objects.create(
            title=title,
            description=description,
            action_type=action_type,
            target_resource=target_resource,
            payload=payload,
            status=ProposalStatus.DRAFT,
            created_by_id=created_by_id,
            constitution_id=constitution_id,
        )

    @staticmethod
    @transaction.atomic
    def submit_proposal(proposal_id: uuid.UUID) -> Proposal:
        """Submit a proposal for policy evaluation.

        Evaluates the proposal against the policy engine and routes it
        based on the decision outcome. Generates approval requests when
        human approval is required.

        Args:
            proposal_id: UUID of the proposal to submit.

        Returns:
            The updated Proposal instance.

        Raises:
            ProposalServiceError: If the proposal doesn't exist.
            InvalidTransitionError: If the proposal is not in DRAFT status.
        """
        try:
            proposal = Proposal.objects.select_for_update().get(id=proposal_id)
        except Proposal.DoesNotExist as e:
            raise ProposalServiceError(f"Proposal {proposal_id} not found") from e

        if proposal.status != ProposalStatus.DRAFT:
            raise InvalidTransitionError(
                f"Proposal must be in DRAFT status to submit, " f"current status: {proposal.status}"
            )

        # Mark as submitted before evaluation
        proposal.status = ProposalStatus.SUBMITTED
        proposal.save(update_fields=["status", "updated_at"])

        # Evaluate against policy engine
        decision = PolicyEngineService.evaluate_action(
            action_type=proposal.action_type,
            target_resource=proposal.target_resource,
            payload=proposal.payload,
            actor_id=proposal.created_by_id,
            constitution_id=proposal.constitution_id,
        )

        # Store decision snapshot
        proposal.policy_decision = PolicyEngineService.get_decision_summary(decision)

        # Route based on decision outcome
        if decision.outcome == DecisionOutcome.DENY:
            proposal.status = ProposalStatus.DENIED
            proposal.save(update_fields=["status", "policy_decision", "updated_at"])
            return proposal

        if decision.outcome == DecisionOutcome.ERROR:
            # Fail-safe: treat ERROR as DENY
            proposal.status = ProposalStatus.DENIED
            proposal.save(update_fields=["status", "policy_decision", "updated_at"])
            return proposal

        if decision.outcome == DecisionOutcome.REQUIRE_HUMAN_APPROVAL:
            proposal.status = ProposalStatus.PENDING_APPROVAL
            proposal.save(update_fields=["status", "policy_decision", "updated_at"])
            ProposalService._create_approval_requests(proposal, decision.requires_approval_from)
            return proposal

        # ALLOW outcome
        proposal.status = ProposalStatus.APPROVED
        proposal.save(update_fields=["status", "policy_decision", "updated_at"])
        return proposal

    @staticmethod
    def _create_approval_requests(proposal: Proposal, required_roles: list[str]) -> None:
        """Generate approval requests for each required role.

        Args:
            proposal: The proposal requiring approval.
            required_roles: List of role names that must approve.
        """
        for role in required_roles:
            ApprovalRequest.objects.create(
                proposal=proposal,
                required_role=role,
                status=ApprovalStatus.PENDING,
            )

    @staticmethod
    @transaction.atomic
    def resolve_approval(
        approval_request_id: uuid.UUID,
        approved: bool,
        decided_by_id: uuid.UUID,
        notes: str = "",
    ) -> ApprovalRequest:
        """Resolve an individual approval request.

        Updates the approval request and checks whether the proposal
        can transition to its final status.

        Args:
            approval_request_id: UUID of the approval request to resolve.
            approved: True to approve, False to reject.
            decided_by_id: UUID of the user making the decision.
            notes: Optional notes from the approver.

        Returns:
            The updated ApprovalRequest instance.

        Raises:
            ProposalServiceError: If the approval request doesn't exist.
            InvalidTransitionError: If the request is not pending.
        """
        try:
            approval_request = (
                ApprovalRequest.objects.select_for_update()
                .select_related("proposal")
                .get(id=approval_request_id)
            )
        except ApprovalRequest.DoesNotExist as e:
            raise ProposalServiceError(f"Approval request {approval_request_id} not found") from e

        if approval_request.status != ApprovalStatus.PENDING:
            raise InvalidTransitionError(
                f"Approval request must be PENDING to resolve, "
                f"current status: {approval_request.status}"
            )

        # Update the approval request
        from django.utils import timezone

        approval_request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        approval_request.decided_by_id = decided_by_id
        approval_request.decided_at = timezone.now()
        approval_request.notes = notes
        approval_request.save(
            update_fields=["status", "decided_by", "decided_at", "notes", "updated_at"]
        )

        # Re-evaluate proposal status based on all approval requests
        ProposalService._update_proposal_after_approval(approval_request.proposal)

        return approval_request

    @staticmethod
    def _update_proposal_after_approval(proposal: Proposal) -> None:
        """Update proposal status based on all its approval requests.

        If any request is rejected, the proposal is DENIED (fail-safe).
        If all requests are approved, the proposal is APPROVED.

        Args:
            proposal: The proposal to update.
        """
        approval_requests = list(ApprovalRequest.objects.filter(proposal=proposal))

        # Any rejection denies the proposal immediately
        has_rejection = any(
            request.status == ApprovalStatus.REJECTED for request in approval_requests
        )
        if has_rejection:
            proposal.status = ProposalStatus.DENIED
            proposal.save(update_fields=["status", "updated_at"])
            return

        # All must be approved to approve the proposal
        all_approved = bool(
            approval_requests
            and all(request.status == ApprovalStatus.APPROVED for request in approval_requests)
        )
        if all_approved:
            proposal.status = ProposalStatus.APPROVED
            proposal.save(update_fields=["status", "updated_at"])

    @staticmethod
    @transaction.atomic
    def execute_proposal(proposal_id: uuid.UUID) -> Proposal:
        """Execute an approved proposal.

        Args:
            proposal_id: UUID of the proposal to execute.

        Returns:
            The updated Proposal instance.

        Raises:
            ProposalServiceError: If the proposal doesn't exist.
            InvalidTransitionError: If the proposal is not approved.
        """
        try:
            proposal = Proposal.objects.select_for_update().get(id=proposal_id)
        except Proposal.DoesNotExist as e:
            raise ProposalServiceError(f"Proposal {proposal_id} not found") from e

        if proposal.status != ProposalStatus.APPROVED:
            raise InvalidTransitionError(
                f"Proposal must be APPROVED to execute, " f"current status: {proposal.status}"
            )

        # TODO: Dispatch actual execution logic based on action_type.
        # This will be implemented in later phases (negotiations, agreements).
        proposal.status = ProposalStatus.EXECUTED
        proposal.save(update_fields=["status", "updated_at"])
        return proposal

    @staticmethod
    @transaction.atomic
    def cancel_proposal(proposal_id: uuid.UUID) -> Proposal:
        """Cancel a proposal that hasn't been executed.

        Also cancels any pending approval requests.

        Args:
            proposal_id: UUID of the proposal to cancel.

        Returns:
            The updated Proposal instance.

        Raises:
            ProposalServiceError: If the proposal doesn't exist.
            InvalidTransitionError: If the proposal is already executed.
        """
        try:
            proposal = Proposal.objects.select_for_update().get(id=proposal_id)
        except Proposal.DoesNotExist as e:
            raise ProposalServiceError(f"Proposal {proposal_id} not found") from e

        if proposal.status == ProposalStatus.EXECUTED:
            raise InvalidTransitionError("Cannot cancel an already executed proposal")

        if proposal.status == ProposalStatus.CANCELLED:
            raise InvalidTransitionError("Proposal is already cancelled")

        proposal.status = ProposalStatus.CANCELLED
        proposal.save(update_fields=["status", "updated_at"])

        # Cancel all pending approval requests
        ApprovalRequest.objects.filter(
            proposal=proposal,
            status=ApprovalStatus.PENDING,
        ).update(status=ApprovalStatus.CANCELLED)

        return proposal
