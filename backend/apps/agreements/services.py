"""
Business services for agreement management.

Handles creation, signing, and verification of agreements.

Source: 04-BUSINESS-FLOW.md Section 10
"""

import logging
from typing import Any, cast

from django.db import transaction
from django.utils import timezone

from apps.agreements.canonical import (
    build_agreement_payload,
    generate_terms_summary,
)
from apps.agreements.models import Agreement, AgreementSignature
from apps.agreements.signing import (
    compute_hash,
    sign_payload,
    verify_signature,
)
from apps.audit.services import create_audit_event
from apps.proposals.models import Proposal
from core.enums import (
    ActorType,
    AgreementStatus,
    EventType,
)
from core.exceptions import AgreementNotInDraftError, HashMismatchError

logger = logging.getLogger("legatio.agreements")


def create_agreement_from_proposal(
    *,
    proposal: Proposal,
    user: Any,
) -> Agreement:
    """
    Create an Agreement from an accepted Proposal.

    Generates the canonical JSON, computes the hash, and creates
    the Agreement in DRAFT status.

    Args:
        proposal: The accepted proposal.
        user: The user creating the agreement.

    Returns:
        The created Agreement in DRAFT status.
    """
    # Get the active constitution version from the room's constitution
    # Note: NegotiationRoom has FK to Constitution, not ConstitutionVersion
    constitution_version = proposal.room.constitution.active_version
    if constitution_version is None:
        raise ValueError(f"Constitution {proposal.room.constitution.id} has no active version")

    # Build canonical payload
    parties = [
        {"id": str(proposal.room.user_agent.id), "role": "buyer"},
        {"id": str(proposal.room.external_agent.id), "role": "seller"},
    ]
    payload = build_agreement_payload(
        proposal_id=str(proposal.id),
        room_id=str(proposal.room.id),
        constitution_version_id=str(constitution_version.id),
        action_type=proposal.action_type,
        amount=str(proposal.amount) if proposal.amount else None,
        currency=proposal.currency,
        terms=proposal.terms,
        parties=parties,
        user_agent_id=str(proposal.room.user_agent.id),
        external_agent_id=str(proposal.room.external_agent.id),
    )

    # Compute hash
    canonical_hash = compute_hash(payload)

    # Generate summary
    terms_summary = generate_terms_summary(
        action_type=proposal.action_type,
        amount=str(proposal.amount) if proposal.amount else None,
        currency=proposal.currency,
        terms=proposal.terms,
    )

    # Generate reference code
    last_agreement = Agreement.objects.order_by("-created_at").first()
    seq = 1
    if last_agreement:
        try:
            seq = int(last_agreement.reference_code.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    year = timezone.now().year
    reference_code = f"AGR-{year}-{seq:06d}"

    # Create agreement
    agreement = Agreement.objects.create(
        reference_code=reference_code,
        room=proposal.room,
        proposal=proposal,
        constitution_version=constitution_version,
        status=AgreementStatus.DRAFT,
        canonical_json=payload,
        canonical_hash=canonical_hash,
        parties=parties,
        terms_summary=terms_summary,
    )

    # Audit event
    create_audit_event(
        event_type=EventType.AGREEMENT_CREATED,
        actor_type=ActorType.USER,
        actor_id=user.id,
        entity_type="Agreement",
        entity_id=agreement.id,
        payload={
            "reference_code": reference_code,
            "proposal_id": str(proposal.id),
            "canonical_hash": canonical_hash,
        },
    )

    logger.info(f"Agreement created: {agreement.reference_code}")
    return cast(Agreement, agreement)


def sign_agreement(
    *,
    agreement: Agreement,
    user: Any,
    ip_address: str | None = None,
    user_agent_string: str | None = None,
) -> AgreementSignature:
    """
    Sign an agreement with HMAC-SHA256.

    This is an atomic operation that:
    1. Verifies the agreement is in DRAFT status.
    2. Verifies the canonical hash matches.
    3. Computes the HMAC-SHA256 signature.
    4. Creates the AgreementSignature.
    5. Updates the Agreement status to SIGNED.
    6. Creates an AuditEvent.

    Source: 04-BUSINESS-FLOW.md Section 10.3

    Args:
        agreement: The agreement to sign.
        user: The user signing the agreement.
        ip_address: IP address of the signer.
        user_agent_string: Browser/client user agent.

    Returns:
        The created AgreementSignature.

    Raises:
        AgreementNotInDraftError: If the agreement is not in DRAFT status.
        HashMismatchError: If the canonical hash doesn't match.
    """
    with transaction.atomic():
        # Lock the agreement
        agreement = Agreement.objects.select_for_update().get(id=agreement.id)

        # Verify status
        if agreement.status != AgreementStatus.DRAFT:
            raise AgreementNotInDraftError(
                f"Agreement {agreement.reference_code} is {agreement.status}, not DRAFT."
            )

        # Verify hash integrity
        recomputed_hash = compute_hash(agreement.canonical_json)
        if recomputed_hash != agreement.canonical_hash:
            raise HashMismatchError("Agreement has been tampered with. Hash mismatch.")

        # Sign
        signature_value = sign_payload(agreement.canonical_hash)

        # Create signature record
        signature = AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            signature_algorithm="HMAC-SHA256",
            signature_value=signature_value,
            signed_payload_hash=agreement.canonical_hash,
            ip_address=ip_address,
            user_agent_string=user_agent_string or "",
        )

        # Update agreement status
        agreement.status = AgreementStatus.SIGNED
        agreement.signed_at = timezone.now()
        agreement.save(update_fields=["status", "signed_at"])

        # Audit event
        create_audit_event(
            event_type=EventType.AGREEMENT_SIGNED,
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="Agreement",
            entity_id=agreement.id,
            payload={
                "reference_code": agreement.reference_code,
                "signature_algorithm": "HMAC-SHA256",
                "signed_payload_hash": agreement.canonical_hash,
            },
        )

        logger.info(f"Agreement signed: {agreement.reference_code}")

    return cast(AgreementSignature, signature)


def verify_agreement_signature(agreement: Agreement) -> bool:
    """
    Verify the signature of a signed agreement.

    Args:
        agreement: The agreement to verify.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not hasattr(agreement, "signature") or not agreement.signature:
        return False

    # Verify hash integrity
    recomputed_hash = compute_hash(agreement.canonical_json)
    if recomputed_hash != agreement.canonical_hash:
        return False

    # Verify signature
    return verify_signature(
        agreement.canonical_hash,
        agreement.signature.signature_value,
    )
