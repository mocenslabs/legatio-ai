"""
Business services for approval management.

Handles creation, processing, and expiration of approval requests.

Source: 04-BUSINESS-FLOW.md Section 9
"""

import logging
from datetime import timedelta
from typing import Any, cast

from django.db import transaction
from django.utils import timezone

from apps.approvals.models import ApprovalDecision, ApprovalRequest
from apps.approvals.summaries import generate_approval_summary
from apps.audit.services import create_audit_event
from apps.notifications.services import (
    notify_approval_decided,
    notify_approval_required,
)
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    ActorType,
    ApprovalStatus,
    EventType,
    ProposalStatus,
)
from core.exceptions import (
    ApprovalAlreadyDecidedError,
    ApprovalExpiredError,
    ApprovalUnauthorizedError,
)

logger = logging.getLogger("legatio.approvals")


def create_approval_request(
    *,
    proposal: Proposal,
    policy_decision: PolicyDecision,
    room: Any,
) -> ApprovalRequest:
    """
    Create an approval request for a proposal.

    This is called when the Policy Engine returns REQUIRE_HUMAN_APPROVAL.

    Args:
        proposal: The proposal requiring approval.
        policy_decision: The policy decision explaining why approval is needed.
        room: The NegotiationRoom.

    Returns:
        The created ApprovalRequest.

    Raises:
        ValueError: If the proposal already has an active approval request.
    """
    # Check if there's already an active request
    existing = ApprovalRequest.objects.filter(
        proposal=proposal,
        status=ApprovalStatus.PENDING,
    ).first()

    if existing:
        raise ValueError(f"Proposal {proposal.id} already has an active approval request")

    # Generate summary
    summary = generate_approval_summary(proposal, policy_decision)

    # Create request
    request = ApprovalRequest.objects.create(
        proposal=proposal,
        room=room,
        requested_by=room.user_agent,
        policy_decision=policy_decision,
        status=ApprovalStatus.PENDING,
        summary=summary,
        expires_at=timezone.now() + timedelta(hours=24),
    )

    # Update proposal status
    proposal.transition_to(ProposalStatus.PENDING_APPROVAL)

    # Audit event
    create_audit_event(
        event_type=EventType.APPROVAL_REQUESTED,
        actor_type=ActorType.SYSTEM,
        entity_type="ApprovalRequest",
        entity_id=request.id,
        payload={
            "proposal_id": str(proposal.id),
            "room_id": str(room.id),
            "summary": summary,
            "expires_at": request.expires_at.isoformat(),
        },
    )

    logger.info(f"ApprovalRequest created: {request.id}")

    # Send WebSocket notification to the user
    owner = getattr(request.room.user_agent, "owner", None)
    if owner is not None and getattr(owner, "id", None) is not None:
        notify_approval_required(
            user_id=owner.id,
            approval_id=request.id,
            summary=request.summary,
            risk_level=policy_decision.risk_level,
            expires_at=request.expires_at.isoformat(),
            negotiation_id=request.room_id,
        )

    return request


def process_approval_decision(
    *,
    request: ApprovalRequest,
    user: Any,
    decision: ApprovalStatus,
    modifications: dict[str, Any] | None = None,
    comment: str | None = None,
) -> ApprovalDecision:
    """
    Process a human decision on an approval request.

    This is an atomic operation that:
    1. Creates an ApprovalDecision record
    2. Updates the ApprovalRequest status
    3. Updates the Proposal status
    4. Creates an AuditEvent

    Source: 04-BUSINESS-FLOW.md Section 9.3

    Args:
        request: The approval request being decided.
        user: The user making the decision.
        decision: The decision (APPROVED, REJECTED, MODIFIED).
        modifications: Optional modifications if decision = MODIFIED.
        comment: Optional user comment.

    Returns:
        The created ApprovalDecision.

    Raises:
        ApprovalAlreadyDecidedError: If the request is already decided.
        ApprovalExpiredError: If the request has expired.
        ApprovalUnauthorizedError: If the user doesn't own the request.
    """
    # Validate decision
    if decision not in [
        ApprovalStatus.APPROVED,
        ApprovalStatus.REJECTED,
        ApprovalStatus.MODIFIED,
    ]:
        raise ValueError(f"Invalid decision: {decision}")

    with transaction.atomic():
        # Lock the request to prevent race conditions
        request = ApprovalRequest.objects.select_for_update().get(id=request.id)

        # Check if already decided
        if request.status != ApprovalStatus.PENDING:
            raise ApprovalAlreadyDecidedError(
                f"Approval request {request.id} is already {request.status}"
            )

        # Check if expired
        if request.expires_at < timezone.now():
            request.transition_to(ApprovalStatus.EXPIRED)
            raise ApprovalExpiredError(f"Approval request {request.id} has expired")

        # Check ownership
        if request.room.user_agent.owner != user:
            raise ApprovalUnauthorizedError("You can only decide on your own approval requests")

        # Create decision record
        approval_decision = cast(
            ApprovalDecision,
            ApprovalDecision.objects.create(
                request=request,
                decided_by=user,
                decision=decision,
                modifications=modifications,
                comment=comment or "",
            ),
        )

        # Update request status
        request.transition_to(decision)

        # Update proposal status
        proposal = request.proposal
        if decision == ApprovalStatus.APPROVED:
            proposal.transition_to(ProposalStatus.ACCEPTED)
            # Note: Agreement generation will be implemented in Phase 5
            logger.info(f"Proposal {proposal.id} approved")
        elif decision in [ApprovalStatus.REJECTED, ApprovalStatus.MODIFIED]:
            proposal.transition_to(ProposalStatus.REJECTED)
            logger.info(f"Proposal {proposal.id} rejected/modified")

        # Audit event
        event_type_map = {
            ApprovalStatus.APPROVED: EventType.APPROVAL_APPROVED,
            ApprovalStatus.REJECTED: EventType.APPROVAL_REJECTED,
            ApprovalStatus.MODIFIED: EventType.APPROVAL_APPROVED,  # Treat as approved
        }

        create_audit_event(
            event_type=event_type_map[decision],
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="ApprovalRequest",
            entity_id=request.id,
            payload={
                "decision": decision,
                "comment": comment,
                "modifications": modifications,
            },
        )

        logger.info(f"ApprovalDecision created: {approval_decision.id}")

        # Send WebSocket notification to the user
        owner = getattr(request.room.user_agent, "owner", None)
        if owner is not None and getattr(owner, "id", None) is not None:
            notify_approval_decided(
                user_id=owner.id,
                approval_id=request.id,
                decision=decision,
            )

    return approval_decision


def expire_stale_approvals() -> int:
    """
    Expire approval requests that have passed their deadline.

    This is called by a Celery Beat task every 5 minutes.

    Returns:
        The number of expired requests.
    """
    stale_requests = ApprovalRequest.objects.filter(
        status=ApprovalStatus.PENDING,
        expires_at__lt=timezone.now(),
    )

    expired_count = 0

    for request in stale_requests:
        try:
            with transaction.atomic():
                # Lock to prevent race conditions
                request = ApprovalRequest.objects.select_for_update().get(id=request.id)

                if request.status != ApprovalStatus.PENDING:
                    continue  # Already decided

                # Expire the request
                request.transition_to(ApprovalStatus.EXPIRED)

                # Create system decision
                ApprovalDecision.objects.create(
                    request=request,
                    decided_by=None,  # System decision
                    decision=ApprovalStatus.EXPIRED,
                    comment="Expired due to timeout",
                )

                # Update proposal status
                request.proposal.transition_to(ProposalStatus.REJECTED)

                # Audit event
                create_audit_event(
                    event_type=EventType.APPROVAL_EXPIRED,
                    actor_type=ActorType.SYSTEM,
                    entity_type="ApprovalRequest",
                    entity_id=request.id,
                    payload={"reason": "expired_timeout"},
                )

                expired_count += 1
                logger.info(f"ApprovalRequest expired: {request.id}")

        except Exception as exc:
            logger.exception(f"Error expiring approval {request.id}: {exc}")
            continue

    return expired_count
