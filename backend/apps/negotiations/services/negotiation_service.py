"""Negotiation Service layer.

This module orchestrates the negotiation lifecycle: creation, offer
exchange, and conclusion. Integrates audit logging and notifications.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction

from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.negotiations.models import (
    Negotiation,
    NegotiationOffer,
    NegotiationStatus,
    OfferStatus,
)
from apps.notifications.models import NotificationType
from apps.notifications.services import NotificationService
from apps.proposals.models import Proposal


class NegotiationServiceError(Exception):
    """Base exception for negotiation service errors."""


class InvalidTransitionError(NegotiationServiceError):
    """Raised when a negotiation state transition is not allowed."""


class NegotiationService:
    """Service layer for negotiation lifecycle operations.

    Orchestrates the full negotiation workflow:
    1. Create negotiation tied to a proposal
    2. Start negotiation (OPEN -> IN_PROGRESS)
    3. Exchange offers with automatic round numbering
    4. Accept, reject, or withdraw offers
    5. Conclude negotiation (AGREED / FAILED / CANCELLED)

    All state transitions are recorded in the audit log with notifications.
    """

    @staticmethod
    @transaction.atomic
    def create_negotiation(
        proposal_id: uuid.UUID,
        title: str,
        description: str,
        initiated_by_id: uuid.UUID,
    ) -> Negotiation:
        """Create a new negotiation tied to a proposal.

        Args:
            proposal_id: The UUID of the proposal being negotiated.
            title: Human-readable title for the negotiation.
            description: Detailed description of the negotiation context.
            initiated_by_id: The UUID of the user initiating the negotiation.

        Returns:
            The created Negotiation instance.

        Raises:
            NegotiationServiceError: If the proposal doesn't exist.
        """
        try:
            proposal = Proposal.objects.get(id=proposal_id)
        except Proposal.DoesNotExist as e:
            raise NegotiationServiceError(f"Proposal {proposal_id} not found") from e

        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title=title,
            description=description,
            status=NegotiationStatus.OPEN,
            initiated_by_id=initiated_by_id,
        )

        AuditService.log_negotiation_event(
            action=AuditAction.NEGOTIATION_CREATED,
            negotiation_id=negotiation.id,
            actor_id=initiated_by_id,
            new_state={"status": negotiation.status, "title": negotiation.title},
            metadata={"proposal_id": str(proposal_id)},
        )

        return negotiation

    @staticmethod
    @transaction.atomic
    def start_negotiation(
        negotiation_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> Negotiation:
        """Start an open negotiation.

        Args:
            negotiation_id: The UUID of the negotiation to start.
            actor_id: Optional UUID of the user starting the negotiation.

        Returns:
            The updated Negotiation instance.

        Raises:
            NegotiationServiceError: If the negotiation doesn't exist.
            InvalidTransitionError: If the negotiation is not OPEN.
        """
        negotiation = NegotiationService._get_negotiation(negotiation_id)

        if negotiation.status != NegotiationStatus.OPEN:
            raise InvalidTransitionError(
                f"Negotiation must be OPEN to start, current status: {negotiation.status}"
            )

        old_state = {"status": negotiation.status}
        negotiation.status = NegotiationStatus.IN_PROGRESS
        negotiation.save(update_fields=["status", "updated_at"])

        AuditService.log_negotiation_event(
            action=AuditAction.NEGOTIATION_STARTED,
            negotiation_id=negotiation.id,
            actor_id=actor_id,
            old_state=old_state,
            new_state={"status": negotiation.status},
        )
        NotificationService.notify_proposal_status(
            proposal_id=negotiation.id,
            recipient_id=negotiation.initiated_by_id,
            notification_type=NotificationType.NEGOTIATION_STARTED,
            title=f"Negotiation started: {negotiation.title}",
            message=f"Your negotiation '{negotiation.title}' has started.",
        )

        return negotiation

    @staticmethod
    @transaction.atomic
    def make_offer(
        negotiation_id: uuid.UUID,
        offered_by_id: uuid.UUID,
        terms: dict[str, Any],
        notes: str = "",
    ) -> NegotiationOffer:
        """Make an offer within a negotiation.

        Automatically assigns the next round number.

        Args:
            negotiation_id: The UUID of the negotiation.
            offered_by_id: The UUID of the user making the offer.
            terms: Structured JSON terms of the offer.
            notes: Optional notes accompanying the offer.

        Returns:
            The created NegotiationOffer instance.

        Raises:
            NegotiationServiceError: If the negotiation doesn't exist.
            InvalidTransitionError: If the negotiation is not active.
        """
        negotiation = NegotiationService._get_negotiation(negotiation_id)

        if not negotiation.is_active:
            raise InvalidTransitionError(
                f"Cannot make an offer on a concluded negotiation "
                f"(status: {negotiation.status})"
            )

        # Calculate next round number
        last_offer = (
            NegotiationOffer.objects.filter(negotiation=negotiation)
            .order_by("-round_number")
            .first()
        )
        next_round = 1 if last_offer is None else last_offer.round_number + 1

        offer = NegotiationOffer.objects.create(
            negotiation=negotiation,
            offered_by_id=offered_by_id,
            terms=terms,
            notes=notes,
            round_number=next_round,
        )

        AuditService.log_negotiation_event(
            action=AuditAction.OFFER_CREATED,
            negotiation_id=negotiation.id,
            actor_id=offered_by_id,
            new_state={"offer_id": str(offer.id), "round_number": next_round},
            metadata={"proposal_id": str(negotiation.proposal_id)},
        )
        NotificationService.notify_proposal_status(
            proposal_id=negotiation.id,
            recipient_id=negotiation.initiated_by_id,
            notification_type=NotificationType.OFFER_RECEIVED,
            title=f"New offer received: {negotiation.title}",
            message=f"A new offer (round {next_round}) was made in '{negotiation.title}'.",
        )

        return offer

    @staticmethod
    @transaction.atomic
    def accept_offer(
        offer_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> NegotiationOffer:
        """Accept an offer, concluding the negotiation as AGREED.

        Args:
            offer_id: The UUID of the offer to accept.
            actor_id: Optional UUID of the user accepting the offer.

        Returns:
            The updated NegotiationOffer instance.

        Raises:
            NegotiationServiceError: If the offer doesn't exist.
            InvalidTransitionError: If the offer is not pending.
        """
        offer = NegotiationService._resolve_offer_transition(
            offer_id=offer_id,
            target_status=OfferStatus.ACCEPTED,
            audit_action=AuditAction.OFFER_ACCEPTED,
            notification_type=NotificationType.OFFER_ACCEPTED,
            actor_id=actor_id,
        )

        # Conclude the negotiation as AGREED
        negotiation = offer.negotiation
        negotiation.status = NegotiationStatus.AGREED
        negotiation.save(update_fields=["status", "updated_at"])

        AuditService.log_negotiation_event(
            action=AuditAction.NEGOTIATION_AGREED,
            negotiation_id=negotiation.id,
            actor_id=actor_id,
            new_state={"status": negotiation.status},
            metadata={"accepted_offer_id": str(offer.id)},
        )

        return offer

    @staticmethod
    @transaction.atomic
    def reject_offer(
        offer_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> NegotiationOffer:
        """Reject an offer.

        Args:
            offer_id: The UUID of the offer to reject.
            actor_id: Optional UUID of the user rejecting the offer.

        Returns:
            The updated NegotiationOffer instance.

        Raises:
            NegotiationServiceError: If the offer doesn't exist.
            InvalidTransitionError: If the offer is not pending.
        """
        return NegotiationService._resolve_offer_transition(
            offer_id=offer_id,
            target_status=OfferStatus.REJECTED,
            audit_action=AuditAction.OFFER_REJECTED,
            notification_type=NotificationType.OFFER_REJECTED,
            actor_id=actor_id,
        )

    @staticmethod
    @transaction.atomic
    def withdraw_offer(
        offer_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> NegotiationOffer:
        """Withdraw an offer. Only the offer creator can withdraw it.

        Args:
            offer_id: The UUID of the offer to withdraw.
            actor_id: The UUID of the user withdrawing the offer.

        Returns:
            The updated NegotiationOffer instance.

        Raises:
            NegotiationServiceError: If the offer doesn't exist or actor is not the creator.
            InvalidTransitionError: If the offer is not pending.
        """
        try:
            offer = NegotiationOffer.objects.select_related("negotiation").get(id=offer_id)
        except NegotiationOffer.DoesNotExist as e:
            raise NegotiationServiceError(f"Offer {offer_id} not found") from e

        if offer.offered_by_id != actor_id:
            raise NegotiationServiceError("Only the offer creator can withdraw it")

        if offer.status != OfferStatus.PENDING:
            raise InvalidTransitionError(
                f"Offer must be PENDING to withdraw, current status: {offer.status}"
            )

        offer.status = OfferStatus.WITHDRAWN
        offer.save(update_fields=["status", "updated_at"])

        AuditService.log_negotiation_event(
            action=AuditAction.OFFER_WITHDRAWN,
            negotiation_id=offer.negotiation_id,
            actor_id=actor_id,
            old_state={"status": OfferStatus.PENDING},
            new_state={"status": offer.status},
            metadata={"offer_id": str(offer.id)},
        )

        return offer

    @staticmethod
    @transaction.atomic
    def conclude_negotiation(
        negotiation_id: uuid.UUID,
        target_status: str,
        actor_id: uuid.UUID | None = None,
    ) -> Negotiation:
        """Conclude a negotiation as FAILED or CANCELLED.

        Args:
            negotiation_id: The UUID of the negotiation to conclude.
            target_status: The target status (FAILED or CANCELLED).
            actor_id: Optional UUID of the user concluding the negotiation.

        Returns:
            The updated Negotiation instance.

        Raises:
            NegotiationServiceError: If the negotiation doesn't exist.
            InvalidTransitionError: If the negotiation is already concluded.
        """
        negotiation = NegotiationService._get_negotiation(negotiation_id)

        if negotiation.is_concluded:
            raise InvalidTransitionError(
                f"Negotiation is already concluded (status: {negotiation.status})"
            )

        old_state = {"status": negotiation.status}
        negotiation.status = target_status
        negotiation.save(update_fields=["status", "updated_at"])

        audit_action = (
            AuditAction.NEGOTIATION_FAILED
            if target_status == NegotiationStatus.FAILED
            else AuditAction.NEGOTIATION_CANCELLED
        )
        AuditService.log_negotiation_event(
            action=audit_action,
            negotiation_id=negotiation.id,
            actor_id=actor_id,
            old_state=old_state,
            new_state={"status": negotiation.status},
        )

        return negotiation

    @staticmethod
    def _get_negotiation(negotiation_id: uuid.UUID) -> Negotiation:
        """Retrieve a negotiation or raise an error.

        Args:
            negotiation_id: The UUID of the negotiation.

        Returns:
            The Negotiation instance.

        Raises:
            NegotiationServiceError: If the negotiation doesn't exist.
        """
        try:
            return Negotiation.objects.select_for_update().get(id=negotiation_id)
        except Negotiation.DoesNotExist as e:
            raise NegotiationServiceError(f"Negotiation {negotiation_id} not found") from e

    @staticmethod
    def _resolve_offer_transition(
        offer_id: uuid.UUID,
        target_status: str,
        audit_action: str,
        notification_type: str,
        actor_id: uuid.UUID | None = None,
    ) -> NegotiationOffer:
        """Resolve an offer transition (ACCEPTED or REJECTED).

        Args:
            offer_id: The UUID of the offer.
            target_status: The target offer status.
            audit_action: The audit action to record.
            notification_type: The notification type to send.
            actor_id: Optional UUID of the user performing the transition.

        Returns:
            The updated NegotiationOffer instance.

        Raises:
            NegotiationServiceError: If the offer doesn't exist.
            InvalidTransitionError: If the offer is not pending.
        """
        try:
            offer = (
                NegotiationOffer.objects.select_for_update()
                .select_related("negotiation")
                .get(id=offer_id)
            )
        except NegotiationOffer.DoesNotExist as e:
            raise NegotiationServiceError(f"Offer {offer_id} not found") from e

        if offer.status != OfferStatus.PENDING:
            raise InvalidTransitionError(
                f"Offer must be PENDING to resolve, current status: {offer.status}"
            )

        offer.status = target_status
        offer.save(update_fields=["status", "updated_at"])

        AuditService.log_negotiation_event(
            action=audit_action,
            negotiation_id=offer.negotiation_id,
            actor_id=actor_id,
            old_state={"status": OfferStatus.PENDING},
            new_state={"status": offer.status},
            metadata={"offer_id": str(offer.id)},
        )
        NotificationService.notify_proposal_status(
            proposal_id=offer.negotiation_id,
            recipient_id=offer.offered_by_id,
            notification_type=notification_type,
            title=f"Offer {target_status.lower()}: round {offer.round_number}",
            message=f"Your offer (round {offer.round_number}) has been {target_status.lower()}.",
        )

        return offer
