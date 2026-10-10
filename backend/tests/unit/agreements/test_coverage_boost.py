"""
Additional tests to boost agreements coverage to >= 95%.
"""

import json
import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.agents.models import Agent
from apps.agreements.admin import (
    AgreementAdmin,
    AgreementSignatureAdmin,
    AgreementSignatureInline,
)
from apps.agreements.canonical import (
    CanonicalEncoder,
    generate_terms_summary,
    to_canonical_json,
)
from apps.agreements.managers import (
    AppendOnlySignatureManager,
    AppendOnlySignatureQuerySet,
    ImmutableAgreementManager,
    ImmutableAgreementQuerySet,
)
from apps.agreements.models import Agreement, AgreementSignature
from apps.agreements.services import create_agreement_from_proposal, sign_agreement
from apps.agreements.signing import sign_agreement_data
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.constitutions.services import activate_version
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import Proposal
from core.enums import (
    AgentType,
    ConstitutionStatus,
    ProposalStatus,
)

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="cov@example.com", password="pass")


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
    version = ConstitutionVersion.objects.create(
        constitution=constitution, version_number=1, created_by=user
    )
    activate_version(version=version, user=user)
    return version


@pytest.fixture
def room(user_agent, external_agent, constitution_version):
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution_version.constitution,
        reference_code="NEG-COV-001",
        title="Test",
        user_instruction="Test",
    )


@pytest.fixture
def proposal(room, external_agent):
    p = Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("700.00"),
        currency="EUR",
        terms={"nights": 5, "destination": "Madrid"},
        status=ProposalStatus.EVALUATING,
        round_number=1,
    )
    Proposal.objects.filter(id=p.id).update(status=ProposalStatus.ACCEPTED)
    p.refresh_from_db()
    return p


@pytest.fixture
def agreement(room, proposal, constitution_version, user):
    return create_agreement_from_proposal(proposal=proposal, user=user)


class TestCanonicalEncoder:
    """Cover CanonicalEncoder.default (lines 36-42)."""

    def test_encoder_handles_uuid(self) -> None:
        """UUID is converted to string."""
        uid = uuid.uuid4()
        data = {"id": uid}
        result = to_canonical_json(data)
        parsed = json.loads(result)
        assert parsed["id"] == str(uid)

    def test_encoder_handles_datetime(self) -> None:
        """datetime is converted to ISO format."""
        dt = datetime(2026, 1, 15, 10, 30, 0)
        data = {"timestamp": dt}
        result = to_canonical_json(data)
        parsed = json.loads(result)
        assert parsed["timestamp"] == "2026-01-15T10:30:00"

    def test_encoder_handles_decimal(self) -> None:
        """Decimal is normalized."""
        data = {"amount": Decimal("100.5000")}
        result = to_canonical_json(data)
        parsed = json.loads(result)
        assert parsed["amount"] == 100.5

    def test_encoder_raises_for_unknown_type(self) -> None:
        """Unknown type raises TypeError."""
        encoder = CanonicalEncoder()

        class Custom:
            pass

        with pytest.raises(TypeError):
            encoder.default(Custom())


class TestGenerateTermsSummary:
    """Cover generate_terms_summary branches (lines 153, 165, 172-178)."""

    def test_subscribe_with_service_and_speed(self) -> None:
        """Subscribe with service and speed."""
        summary = generate_terms_summary(
            action_type="subscribe",
            amount="70.00",
            currency="EUR",
            terms={"service": "internet", "speed": "600Mbps"},
        )
        assert "Subscription" in summary
        assert "internet" in summary
        assert "600Mbps" in summary
        assert "EUR 70.00" in summary

    def test_other_action_type(self) -> None:
        """Other action types are capitalized."""
        summary = generate_terms_summary(
            action_type="share_data",
            amount=None,
            currency=None,
            terms={"fields": ["email"]},
        )
        assert "Share_data" in summary

    def test_purchase_with_product(self) -> None:
        """Purchase with product field."""
        summary = generate_terms_summary(
            action_type="purchase",
            amount="100.00",
            currency="EUR",
            terms={"product": "laptop"},
        )
        assert "Purchase" in summary
        assert "laptop" in summary

    def test_extra_flags(self) -> None:
        """Extra flags like cancellation and breakfast are shown."""
        summary = generate_terms_summary(
            action_type="purchase",
            amount="100.00",
            currency="EUR",
            terms={
                "cancellation": "free",
                "breakfast": True,
                "auto_renewal": False,
            },
        )
        assert "free cancellation" in summary
        assert "breakfast included" in summary
        assert "no auto-renewal" in summary

    def test_no_amount_no_currency(self) -> None:
        """No amount and no currency produces minimal summary."""
        summary = generate_terms_summary(
            action_type="share_data",
            amount=None,
            currency=None,
            terms={},
        )
        assert isinstance(summary, str)


@pytest.mark.django_db
class TestManagers:
    """Cover manager methods (lines 17-19, 33, 36)."""

    def test_immutable_queryset_update_on_signed_raises(self, agreement) -> None:
        """Bulk update on signed agreements raises RuntimeError."""
        sign_agreement(agreement=agreement, user=agreement.room.user_agent.owner)
        with pytest.raises(RuntimeError, match="Cannot update"):
            Agreement.objects.filter(id=agreement.id).update(status="VOIDED")

    def test_append_only_queryset_update_raises(self, agreement) -> None:
        """Bulk update on signatures raises RuntimeError."""
        sign_agreement(agreement=agreement, user=agreement.room.user_agent.owner)
        with pytest.raises(RuntimeError, match="append-only"):
            AgreementSignature.objects.filter(agreement=agreement).update(signature_value="new")

    def test_append_only_queryset_delete_raises(self, agreement) -> None:
        """Bulk delete on signatures raises RuntimeError."""
        sign_agreement(agreement=agreement, user=agreement.room.user_agent.owner)
        with pytest.raises(RuntimeError, match="append-only"):
            AgreementSignature.objects.filter(agreement=agreement).delete()

    def test_immutable_queryset_update_on_draft_allowed(self, agreement) -> None:
        """Bulk update on draft agreements is allowed."""
        count = Agreement.objects.filter(id=agreement.id).update(terms_summary="Updated summary")
        assert count == 1

    def test_managers_get_queryset(self) -> None:
        """Managers return correct QuerySet types."""
        assert isinstance(Agreement.objects.get_queryset(), ImmutableAgreementQuerySet)
        assert isinstance(AgreementSignature.objects.get_queryset(), AppendOnlySignatureQuerySet)
        assert isinstance(Agreement.objects, ImmutableAgreementManager)
        assert isinstance(AgreementSignature.objects, AppendOnlySignatureManager)


@pytest.mark.django_db
class TestAdmin:
    """Cover admin.py methods."""

    def test_agreement_signature_inline_permissions(self) -> None:
        """Inline has no add/change/delete permissions."""
        site = AdminSite()
        inline = AgreementSignatureInline(AgreementSignature, site)
        request = RequestFactory().get("/admin/")
        assert inline.has_add_permission(request, obj=None) is False
        assert inline.has_change_permission(request, obj=None) is False
        assert inline.has_delete_permission(request, obj=None) is False

    def test_agreement_admin_signer_email_signed(self, agreement, user) -> None:
        """signer_email returns email when signed."""
        sign_agreement(agreement=agreement, user=user)
        agreement.refresh_from_db()
        site = AdminSite()
        admin_instance = AgreementAdmin(Agreement, site)
        email = admin_instance.signer_email(agreement)
        assert email == user.email

    def test_agreement_admin_signer_email_unsigned(self, agreement) -> None:
        """signer_email returns 'Not signed' when unsigned."""
        site = AdminSite()
        admin_instance = AgreementAdmin(Agreement, site)
        email = admin_instance.signer_email(agreement)
        assert email == "Not signed"

    def test_agreement_admin_permissions(self) -> None:
        """AgreementAdmin has no add/change/delete permissions."""
        site = AdminSite()
        admin_instance = AgreementAdmin(Agreement, site)
        request = RequestFactory().get("/admin/")
        assert admin_instance.has_add_permission(request) is False
        assert admin_instance.has_change_permission(request, obj=None) is False
        assert admin_instance.has_delete_permission(request, obj=None) is False

    def test_agreement_signature_admin_permissions(self) -> None:
        """AgreementSignatureAdmin has no add/change/delete permissions."""
        site = AdminSite()
        admin_instance = AgreementSignatureAdmin(AgreementSignature, site)
        request = RequestFactory().get("/admin/")
        assert admin_instance.has_add_permission(request) is False
        assert admin_instance.has_change_permission(request, obj=None) is False
        assert admin_instance.has_delete_permission(request, obj=None) is False


class TestSignAgreementData:
    """Cover full pipeline."""

    def test_sign_agreement_data_returns_tuple(self) -> None:
        """sign_agreement_data returns (json, hash, signature)."""
        data = {"test": "data"}
        result = sign_agreement_data(data)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)
        assert isinstance(result[2], str)


@pytest.mark.django_db
class TestServicesEdgeCases:
    """Cover service edge cases."""

    def test_no_active_version_raises(self, user, user_agent, external_agent, constitution) -> None:
        """create_agreement_from_proposal raises when no active version."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-NOACTIVE",
            title="Test",
            user_instruction="Test",
        )
        p = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            terms={},
            status=ProposalStatus.EVALUATING,
            round_number=1,
        )
        Proposal.objects.filter(id=p.id).update(status=ProposalStatus.ACCEPTED)
        p.refresh_from_db()
        with pytest.raises(ValueError, match="no active version"):
            create_agreement_from_proposal(proposal=p, user=user)
