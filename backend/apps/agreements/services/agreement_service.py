"""Agreement Service layer.

This module orchestrates the agreement lifecycle: creation, generation from
proposals, activation, amendments, and termination. It provides automatic
versioning for every significant change, and integrates audit logging and
notifications.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.agreements.models import Agreement, AgreementStatus, AgreementVersion
from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.notifications.models import NotificationType
from apps.notifications.services import NotificationService
from apps.proposals.models import Proposal, ProposalStatus


class AgreementServiceError(Exception):
    """Base exception for agreement service errors."""


class InvalidTransitionError(AgreementServiceError):
    """Raised when an agreement state transition is not allowed."""


class AgreementService:
    """Service layer for agreement lifecycle operations.

    Orchestrates the full agreement workflow:
    1. Create agreement (DRAFT) directly or from an executed proposal
    2. Activate agreement (sets effective_date)
    3. Amend agreement (creates new version)
    4. Suspend, complete, or terminate agreement

    All significant changes create a version snapshot, and all state
    transitions are recorded in the audit log with notifications sent
    to the agreement creator.
    """

    @staticmethod
    @transaction.atomic
    def create_agreement(
        title: str,
        terms: dict[str, Any],
        created_by_id: uuid.UUID,
        description: str = "",
        proposal_id: uuid.UUID | None = None,
        constitution_id: uuid.UUID | None = None,
    ) -> Agreement:
        """Create a new agreement in DRAFT status.

        Args:
            title: Human-readable title for the agreement.
            terms: Structured JSON terms of the agreement.
            created_by_id: UUID of the user creating the agreement.
            description: Optional detailed description.
            proposal_id: Optional UUID of the originating proposal.
            constitution_id: Optional UUID of the constitution.

        Returns:
            The created Agreement instance.
        """
        agreement = Agreement.objects.create(
            title=title,
            description=description,
            terms=terms,
            status=AgreementStatus.DRAFT,
            created_by_id=created_by_id,
            proposal_id=proposal_id,
            constitution_id=constitution_id,
        )

        # Create the initial version snapshot
        AgreementService._create_version(
            agreement, change_reason="Initial version", actor_id=created_by_id
        )

        AuditService.log_agreement_event(
            action=AuditAction.AGREEMENT_CREATED,
            agreement_id=agreement.id,
            actor_id=created_by_id,
            new_state={"status": agreement.status, "title": agreement.title},
        )

        return agreement

    @staticmethod
    @transaction.atomic
    def generate_from_proposal(
        proposal_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> Agreement:
        """Generate an agreement from an executed proposal.

        Args:
            proposal_id: UUID of the executed proposal.
            actor_id: Optional UUID of the user generating the agreement.

        Returns:
            The created Agreement instance.

        Raises:
            AgreementServiceError: If the proposal doesn't exist.
            InvalidTransitionError: If the proposal is not executed.
        """
        try:
            proposal = Proposal.objects.get(id=proposal_id)
        except Proposal.DoesNotExist as e:
            raise AgreementServiceError(f"Proposal {proposal_id} not found") from e

        if proposal.status != ProposalStatus.EXECUTED:
            raise InvalidTransitionError(
                f"Proposal must be EXECUTED to generate an agreement, "
                f"current status: {proposal.status}"
            )

        creator_id = actor_id if actor_id is not None else proposal.created_by_id

        agreement = Agreement.objects.create(
            title=proposal.title,
            description=proposal.description,
            terms=proposal.payload,
            status=AgreementStatus.DRAFT,
            created_by_id=creator_id,
            proposal=proposal,
            constitution=proposal.constitution,
        )

        AgreementService._create_version(
            agreement,
            change_reason=f"Generated from proposal {proposal_id}",
            actor_id=creator_id,
        )

        AuditService.log_agreement_event(
            action=AuditAction.AGREEMENT_CREATED,
            agreement_id=agreement.id,
            actor_id=creator_id,
            new_state={"status": agreement.status, "title": agreement.title},
            metadata={"proposal_id": str(proposal_id)},
        )

        return agreement

    @staticmethod
    @transaction.atomic
    def activate_agreement(
        agreement_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> Agreement:
        """Activate a draft agreement.

        Sets the effective_date to now if not already set.

        Args:
            agreement_id: UUID of the agreement to activate.
            actor_id: Optional UUID of the user activating the agreement.

        Returns:
            The updated Agreement instance.

        Raises:
            AgreementServiceError: If the agreement doesn't exist.
            InvalidTransitionError: If the agreement is not in DRAFT status.
        """
        try:
            agreement = Agreement.objects.select_for_update().get(id=agreement_id)
        except Agreement.DoesNotExist as e:
            raise AgreementServiceError(f"Agreement {agreement_id} not found") from e

        if agreement.status != AgreementStatus.DRAFT:
            raise InvalidTransitionError(
                f"Agreement must be DRAFT to activate, " f"current status: {agreement.status}"
            )

        old_state = {"status": agreement.status}

        agreement.status = AgreementStatus.ACTIVE
        if agreement.effective_date is None:
            agreement.effective_date = timezone.now()
        agreement.save(update_fields=["status", "effective_date", "updated_at"])

        AuditService.log_agreement_event(
            action=AuditAction.AGREEMENT_ACTIVATED,
            agreement_id=agreement.id,
            actor_id=actor_id,
            old_state=old_state,
            new_state={"status": agreement.status},
        )
        NotificationService.notify_proposal_status(
            proposal_id=agreement.id,
            recipient_id=agreement.created_by_id,
            notification_type=NotificationType.AGREEMENT_ACTIVATED,
            title=f"Agreement activated: {agreement.title}",
            message=f"Your agreement '{agreement.title}' is now active.",
        )

        return agreement

    @staticmethod
    @transaction.atomic
    def amend_agreement(
        agreement_id: uuid.UUID,
        terms: dict[str, Any],
        change_reason: str,
        actor_id: uuid.UUID | None = None,
        title: str | None = None,
    ) -> Agreement:
        """Amend an agreement, creating a new version.

        Only active agreements can be amended.

        Args:
            agreement_id: UUID of the agreement to amend.
            terms: New terms for the agreement.
            change_reason: Description of why the amendment is made.
            actor_id: Optional UUID of the user making the amendment.
            title: Optional new title for the agreement.

        Returns:
            The updated Agreement instance.

        Raises:
            AgreementServiceError: If the agreement doesn't exist.
            InvalidTransitionError: If the agreement is not ACTIVE.
        """
        try:
            agreement = Agreement.objects.select_for_update().get(id=agreement_id)
        except Agreement.DoesNotExist as e:
            raise AgreementServiceError(f"Agreement {agreement_id} not found") from e

        if agreement.status != AgreementStatus.ACTIVE:
            raise InvalidTransitionError(
                f"Agreement must be ACTIVE to amend, " f"current status: {agreement.status}"
            )

        old_state = {"status": agreement.status, "terms": agreement.terms}

        agreement.terms = terms
        if title is not None:
            agreement.title = title
        agreement.save(update_fields=["terms", "title", "updated_at"])

        # Create a new version snapshot for the amendment
        AgreementService._create_version(agreement, change_reason=change_reason, actor_id=actor_id)

        AuditService.log_agreement_event(
            action=AuditAction.AGREEMENT_AMENDED,
            agreement_id=agreement.id,
            actor_id=actor_id,
            old_state=old_state,
            new_state={"status": agreement.status, "terms": agreement.terms},
            metadata={"change_reason": change_reason},
        )

        return agreement

    @staticmethod
    @transaction.atomic
    def complete_agreement(
        agreement_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> Agreement:
        """Complete an active agreement.

        Args:
            agreement_id: UUID of the agreement to complete.
            actor_id: Optional UUID of the user completing the agreement.

        Returns:
            The updated Agreement instance.

        Raises:
            AgreementServiceError: If the agreement doesn't exist.
            InvalidTransitionError: If the agreement is not ACTIVE.
        """
        return AgreementService._transition_to_final(
            agreement_id=agreement_id,
            target_status=AgreementStatus.COMPLETED,
            audit_action=AuditAction.AGREEMENT_COMPLETED,
            notification_type=NotificationType.AGREEMENT_COMPLETED,
            actor_id=actor_id,
        )

    @staticmethod
    @transaction.atomic
    def terminate_agreement(
        agreement_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        reason: str = "",
    ) -> Agreement:
        """Terminate an active agreement.

        Args:
            agreement_id: UUID of the agreement to terminate.
            actor_id: Optional UUID of the user terminating the agreement.
            reason: Optional reason for termination.

        Returns:
            The updated Agreement instance.

        Raises:
            AgreementServiceError: If the agreement doesn't exist.
            InvalidTransitionError: If the agreement is not ACTIVE.
        """
        return AgreementService._transition_to_final(
            agreement_id=agreement_id,
            target_status=AgreementStatus.TERMINATED,
            audit_action=AuditAction.AGREEMENT_TERMINATED,
            notification_type=NotificationType.AGREEMENT_TERMINATED,
            actor_id=actor_id,
            reason=reason,
        )

    @staticmethod
    def _transition_to_final(
        agreement_id: uuid.UUID,
        target_status: str,
        audit_action: str,
        notification_type: str,
        actor_id: uuid.UUID | None = None,
        reason: str = "",
    ) -> Agreement:
        """Transition an agreement to a final status (COMPLETED or TERMINATED).

        Args:
            agreement_id: UUID of the agreement.
            target_status: The target status to transition to.
            audit_action: The audit action to record.
            notification_type: The notification type to send.
            actor_id: Optional UUID of the user performing the transition.
            reason: Optional reason for the transition.

        Returns:
            The updated Agreement instance.

        Raises:
            AgreementServiceError: If the agreement doesn't exist.
            InvalidTransitionError: If the agreement is not ACTIVE.
        """
        try:
            agreement = Agreement.objects.select_for_update().get(id=agreement_id)
        except Agreement.DoesNotExist as e:
            raise AgreementServiceError(f"Agreement {agreement_id} not found") from e

        if agreement.status != AgreementStatus.ACTIVE:
            raise InvalidTransitionError(
                f"Agreement must be ACTIVE to transition, " f"current status: {agreement.status}"
            )

        old_state = {"status": agreement.status}

        agreement.status = target_status
        agreement.save(update_fields=["status", "updated_at"])

        AuditService.log_agreement_event(
            action=audit_action,
            agreement_id=agreement.id,
            actor_id=actor_id,
            old_state=old_state,
            new_state={"status": agreement.status},
            metadata={"reason": reason} if reason else None,
        )
        NotificationService.notify_proposal_status(
            proposal_id=agreement.id,
            recipient_id=agreement.created_by_id,
            notification_type=notification_type,
            title=f"Agreement {target_status.lower()}: {agreement.title}",
            message=f"Your agreement '{agreement.title}' has been {target_status.lower()}.",
        )

        return agreement

    @staticmethod
    def _create_version(
        agreement: Agreement,
        change_reason: str,
        actor_id: uuid.UUID | None = None,
    ) -> AgreementVersion:
        """Create a new version snapshot for an agreement.

        Args:
            agreement: The agreement to version.
            change_reason: Description of why the version is created.
            actor_id: Optional UUID of the user creating the version.

        Returns:
            The created AgreementVersion instance.
        """
        last_version = (
            AgreementVersion.objects.filter(agreement=agreement).order_by("-version_number").first()
        )
        next_number = 1 if last_version is None else last_version.version_number + 1

        creator_id = actor_id if actor_id is not None else agreement.created_by_id

        return AgreementVersion.objects.create(
            agreement=agreement,
            version_number=next_number,
            title=agreement.title,
            terms=agreement.terms,
            change_reason=change_reason,
            created_by_id=creator_id,
        )
