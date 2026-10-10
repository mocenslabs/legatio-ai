"""
Unit tests for Agreement and AgreementSignature models.
Source: 03-DATA-MODEL.md Section 12
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.agents.models import Agent
from apps.agreements.models import Agreement, AgreementSignature
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import Proposal
from core.enums import (
    AgentType,
    AgreementStatus,
    ConstitutionStatus,
    ProposalStatus,
)

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent():
    return Agent.objects.create(owner=None, agent_type=AgentType.EXTERNAL_AGENT, name="Hotel Agent")


@pytest.fixture
def constitution(user, user_agent):
    return Constitution.objects.create(
        agent=user_agent, name="Travel", status=ConstitutionStatus.ACTIVE
    )


@pytest.fixture
def constitution_version(user, constitution):
    return ConstitutionVersion.objects.create(
        constitution=constitution, version_number=1, created_by=user
    )


@pytest.fixture
def room(user_agent, external_agent, constitution):
    # NegotiationRoom uses 'constitution' FK, not 'constitution_version'
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-2026-0001",
        title="Hotel Madrid",
        user_instruction="Find hotel",
    )


@pytest.fixture
def proposal(room, external_agent):
    """Create a proposal in ACCEPTED status bypassing the state machine.

    The Agreement tests are not testing the Proposal state machine,
    so we use QuerySet.update() to set the status directly.
    """
    p = Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("700.00"),
        currency="EUR",
        status=ProposalStatus.EVALUATING,
        round_number=1,
    )
    # Bypass state machine: directly set ACCEPTED for test setup
    Proposal.objects.filter(id=p.id).update(status=ProposalStatus.ACCEPTED)
    p.refresh_from_db()
    return p


@pytest.fixture
def agreement(room, proposal, constitution_version):
    return Agreement.objects.create(
        reference_code="AGR-2026-000001",
        room=room,
        proposal=proposal,
        constitution_version=constitution_version,
        status=AgreementStatus.DRAFT,
        canonical_json={"amount": "700.00", "currency": "EUR"},
        canonical_hash="a" * 64,
        parties=[{"id": str(room.user_agent.id), "role": "buyer"}],
        terms_summary="Hotel for 5 nights at €700",
    )


@pytest.mark.django_db
class TestAgreementModel:
    def test_create_agreement(self, agreement) -> None:
        """Agreement can be created in DRAFT status."""
        assert agreement.status == AgreementStatus.DRAFT
        assert agreement.reference_code == "AGR-2026-000001"
        assert agreement.canonical_hash == "a" * 64

    def test_agreement_id_is_uuid(self, agreement) -> None:
        """Agreement ID is a UUID."""
        import uuid as uuid_module

        assert isinstance(agreement.id, uuid_module.UUID)

    def test_update_draft_allowed(self, agreement) -> None:
        """Draft agreements can be updated."""
        agreement.status = AgreementStatus.SIGNED
        agreement.save()
        agreement.refresh_from_db()
        assert agreement.status == AgreementStatus.SIGNED

    def test_update_signed_forbidden(self, agreement, user) -> None:
        """Signed agreements cannot be updated."""
        agreement.status = AgreementStatus.SIGNED
        agreement.save()
        agreement.status = AgreementStatus.VOIDED
        with pytest.raises(RuntimeError, match="cannot be modified"):
            agreement.save()

    def test_delete_forbidden(self, agreement) -> None:
        """Agreements cannot be deleted."""
        with pytest.raises(RuntimeError, match="cannot be deleted"):
            agreement.delete()

    def test_unique_canonical_hash(self, room, proposal, constitution_version) -> None:
        """canonical_hash must be unique."""
        Agreement.objects.create(
            reference_code="AGR-2026-000002",
            room=room,
            proposal=proposal,
            constitution_version=constitution_version,
            status=AgreementStatus.DRAFT,
            canonical_json={"amount": "800.00"},
            canonical_hash="b" * 64,
            parties=[],
            terms_summary="Test",
        )
        with pytest.raises(IntegrityError):
            Agreement.objects.create(
                reference_code="AGR-2026-000003",
                room=room,
                proposal=proposal,
                constitution_version=constitution_version,
                status=AgreementStatus.DRAFT,
                canonical_json={"amount": "900.00"},
                canonical_hash="b" * 64,  # Duplicate hash
                parties=[],
                terms_summary="Test",
            )


@pytest.mark.django_db
class TestAgreementSignatureModel:
    def test_create_signature(self, agreement, user) -> None:
        """Signature can be created with matching hash."""
        signature = AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            signature_algorithm="HMAC-SHA256",
            signature_value="sig_value_here",
            signed_payload_hash=agreement.canonical_hash,
            ip_address="192.168.1.1",
            user_agent_string="Mozilla/5.0",
        )
        assert signature.signer == user
        assert signature.signed_payload_hash == agreement.canonical_hash

    def test_hash_mismatch_forbidden(self, agreement, user) -> None:
        """Signature creation fails if hash does not match."""
        with pytest.raises(ValueError, match="must exactly match"):
            AgreementSignature.objects.create(
                agreement=agreement,
                signer=user,
                signature_algorithm="HMAC-SHA256",
                signature_value="sig_value",
                signed_payload_hash="wrong_hash",  # Mismatch!
            )

    def test_update_forbidden(self, agreement, user) -> None:
        """Signatures cannot be updated."""
        signature = AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            signature_algorithm="HMAC-SHA256",
            signature_value="sig_value",
            signed_payload_hash=agreement.canonical_hash,
        )
        signature.signature_value = "new_sig"
        with pytest.raises(RuntimeError, match="append-only"):
            signature.save()

    def test_delete_forbidden(self, agreement, user) -> None:
        """Signatures cannot be deleted."""
        signature = AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            signature_algorithm="HMAC-SHA256",
            signature_value="sig_value",
            signed_payload_hash=agreement.canonical_hash,
        )
        with pytest.raises(RuntimeError, match="append-only"):
            signature.delete()

    def test_cascade_delete_agreement_deletes_signature(self, agreement, user) -> None:
        """Deleting agreement (via hard delete bypass) deletes signature."""
        signature = AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            signature_algorithm="HMAC-SHA256",
            signature_value="sig_value",
            signed_payload_hash=agreement.canonical_hash,
        )
        signature_id = signature.id
        # Bypass manager delete restriction for testing cascade
        Agreement.objects.filter(id=agreement.id).delete()
        assert not AgreementSignature.objects.filter(id=signature_id).exists()
