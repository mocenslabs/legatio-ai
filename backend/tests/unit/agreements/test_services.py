"""
Unit tests for agreement services.
Source: 04-BUSINESS-FLOW.md Section 10
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.agreements.models import Agreement, AgreementSignature
from apps.agreements.services import (
    create_agreement_from_proposal,
    sign_agreement,
    verify_agreement_signature,
)
from apps.agreements.signing import compute_hash
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.constitutions.services import activate_version
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import Proposal
from core.enums import (
    AgentType,
    AgreementStatus,
    ConstitutionStatus,
    ProposalStatus,
)
from core.exceptions import AgreementNotInDraftError

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
    """Create AND activate the constitution version."""
    version = ConstitutionVersion.objects.create(
        constitution=constitution, version_number=1, created_by=user
    )
    activate_version(version=version, user=user)
    return version


@pytest.fixture
def room(user_agent, external_agent, constitution_version):
    """Room depends on constitution_version to ensure it is activated first."""
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution_version.constitution,
        reference_code="NEG-2026-0001",
        title="Hotel Madrid",
        user_instruction="Find hotel",
    )


@pytest.fixture
def accepted_proposal(room, external_agent):
    """Create a proposal in ACCEPTED status bypassing the state machine."""
    p = Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("700.00"),
        currency="EUR",
        terms={"nights": 5, "destination": "Madrid", "cancellation": "48h"},
        status=ProposalStatus.EVALUATING,
        round_number=3,
    )
    # Bypass state machine for test setup
    Proposal.objects.filter(id=p.id).update(status=ProposalStatus.ACCEPTED)
    p.refresh_from_db()
    return p


@pytest.mark.django_db
class TestCreateAgreement:
    def test_create_agreement(self, accepted_proposal, user) -> None:
        """Agreement can be created from accepted proposal."""
        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        assert agreement.status == AgreementStatus.DRAFT
        assert agreement.reference_code.startswith("AGR-")
        assert agreement.canonical_hash is not None
        assert len(agreement.canonical_hash) == 64
        assert agreement.terms_summary is not None
        assert "Madrid" in agreement.terms_summary

    def test_create_agreement_creates_audit_event(self, accepted_proposal, user) -> None:
        """Creating agreement creates audit event."""
        from apps.audit.models import AuditEvent

        initial_count = AuditEvent.objects.count()
        create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        assert AuditEvent.objects.count() == initial_count + 1

    def test_canonical_hash_is_correct(self, accepted_proposal, user) -> None:
        """Canonical hash matches recomputed hash."""
        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        recomputed = compute_hash(agreement.canonical_json)
        assert agreement.canonical_hash == recomputed

    def test_reference_code_increments(self, accepted_proposal, user) -> None:
        """Reference code increments for subsequent agreements."""
        agreement1 = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        # Create a second proposal/room for another agreement
        room2 = NegotiationRoom.objects.create(
            user_agent=accepted_proposal.room.user_agent,
            external_agent=accepted_proposal.room.external_agent,
            constitution=accepted_proposal.room.constitution,
            reference_code="NEG-2026-0002",
            title="Hotel Barcelona",
            user_instruction="Find hotel",
        )
        p2 = Proposal.objects.create(
            room=room2,
            sender=accepted_proposal.room.external_agent,
            action_type="purchase",
            amount=Decimal("500.00"),
            currency="EUR",
            terms={},
            status=ProposalStatus.EVALUATING,
            round_number=1,
        )
        Proposal.objects.filter(id=p2.id).update(status=ProposalStatus.ACCEPTED)
        p2.refresh_from_db()

        agreement2 = create_agreement_from_proposal(proposal=p2, user=user)
        seq1 = int(agreement1.reference_code.split("-")[-1])
        seq2 = int(agreement2.reference_code.split("-")[-1])
        assert seq2 == seq1 + 1


@pytest.mark.django_db
class TestSignAgreement:
    def test_sign_agreement(self, accepted_proposal, user) -> None:
        """Agreement can be signed."""
        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        signature = sign_agreement(agreement=agreement, user=user)
        assert isinstance(signature, AgreementSignature)
        assert signature.signature_algorithm == "HMAC-SHA256"
        assert len(signature.signature_value) == 64
        assert signature.signed_payload_hash == agreement.canonical_hash
        agreement.refresh_from_db()
        assert agreement.status == AgreementStatus.SIGNED
        assert agreement.signed_at is not None

    def test_sign_creates_audit_event(self, accepted_proposal, user) -> None:
        """Signing creates audit event."""
        from apps.audit.models import AuditEvent

        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        initial_count = AuditEvent.objects.count()
        sign_agreement(agreement=agreement, user=user)
        assert AuditEvent.objects.count() == initial_count + 1

    def test_sign_non_draft_raises(self, accepted_proposal, user) -> None:
        """Cannot sign a non-DRAFT agreement."""
        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        sign_agreement(agreement=agreement, user=user)
        with pytest.raises(AgreementNotInDraftError):
            sign_agreement(agreement=agreement, user=user)

    def test_sign_with_ip_and_user_agent(self, accepted_proposal, user) -> None:
        """Signature records IP and user agent."""
        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        signature = sign_agreement(
            agreement=agreement,
            user=user,
            ip_address="192.168.1.1",
            user_agent_string="Mozilla/5.0",
        )
        assert signature.ip_address == "192.168.1.1"
        assert signature.user_agent_string == "Mozilla/5.0"

    def test_sign_hash_mismatch_raises(self, accepted_proposal, user) -> None:
        """Signing detects hash mismatch (tampering)."""
        from core.exceptions import HashMismatchError

        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        # Tamper with canonical_hash via QuerySet to bypass model save()
        Agreement.objects.filter(id=agreement.id).update(canonical_hash="0" * 64)
        agreement.refresh_from_db()
        with pytest.raises(HashMismatchError):
            sign_agreement(agreement=agreement, user=user)


@pytest.mark.django_db
class TestVerifyAgreementSignature:
    def test_verify_valid_signature(self, accepted_proposal, user) -> None:
        """Valid signature passes verification."""
        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        sign_agreement(agreement=agreement, user=user)
        agreement.refresh_from_db()
        assert verify_agreement_signature(agreement) is True

    def test_verify_unsigned_agreement(self, accepted_proposal, user) -> None:
        """Unsigned agreement fails verification."""
        agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
        assert verify_agreement_signature(agreement) is False

        def test_verify_tampered_hash_fails(self, accepted_proposal, user) -> None:
            """Tampered canonical_json fails verification."""
            import json as json_mod

            from django.db import connection

            agreement = create_agreement_from_proposal(proposal=accepted_proposal, user=user)
            sign_agreement(agreement=agreement, user=user)
            # Tamper canonical_json via raw SQL to bypass manager restrictions.
            # This simulates a real attack where someone modifies the DB directly.
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE legatio_agreements_agreement
                           SET canonical_json = %s
                           WHERE id = %s""",
                    [json_mod.dumps({"tampered": True}), agreement.id],
                )
            agreement.refresh_from_db()
            assert verify_agreement_signature(agreement) is False
