"""
Integration tests for Agreement API endpoints.

Source: 05-ROADMAP.md Section 9.5
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services.auth import generate_access_token
from apps.agents.models import Agent
from apps.agreements.services import (
    create_agreement_from_proposal,
    sign_agreement,
)
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

User = get_user_model()


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(email="agreement_api@example.com", password="pass1234")


@pytest.fixture
def user_agent(user):
    """Create a user agent."""
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="User Agent",
    )


@pytest.fixture
def external_agent():
    """Create an external agent."""
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.EXTERNAL_AGENT,
        name="Hotel Agent",
    )


@pytest.fixture
def constitution(user, user_agent):
    """Create an active constitution with active version."""
    const = Constitution.objects.create(
        agent=user_agent,
        name="Travel Rules",
        status=ConstitutionStatus.ACTIVE,
    )
    version = ConstitutionVersion.objects.create(
        constitution=const,
        version_number=1,
        created_by=user,
    )
    activate_version(version=version, user=user)
    return const


@pytest.fixture
def room(user_agent, external_agent, constitution):
    """Create a negotiation room."""
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-AGR-001",
        title="Hotel Madrid",
        user_instruction="Find hotel",
    )


@pytest.fixture
def accepted_proposal(room, external_agent):
    """Create an accepted proposal bypassing state machine."""
    p = Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("700.00"),
        currency="EUR",
        terms={"nights": 5, "destination": "Madrid"},
        status=ProposalStatus.EVALUATING,
        round_number=3,
    )
    Proposal.objects.filter(id=p.id).update(status=ProposalStatus.ACCEPTED)
    p.refresh_from_db()
    return p


@pytest.fixture
def draft_agreement(accepted_proposal, user):
    """Create a draft agreement."""
    return create_agreement_from_proposal(
        proposal=accepted_proposal,
        user=user,
    )


@pytest.fixture
def signed_agreement(draft_agreement, user):
    """Create a signed agreement."""
    sign_agreement(agreement=draft_agreement, user=user)
    draft_agreement.refresh_from_db()
    return draft_agreement


@pytest.mark.django_db
class TestAgreementListAPI:
    def test_list_agreements(self, user, signed_agreement) -> None:
        """User can list their agreements."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/agreements/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        if isinstance(data, dict) and "results" in data:
            data = data["results"]
        assert len(data) >= 1

    def test_list_agreements_unauthenticated(self) -> None:
        """Unauthenticated users cannot list agreements."""
        client = APIClient()
        response = client.get("/api/v1/agreements/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAgreementRetrieveAPI:
    def test_retrieve_agreement(self, user, signed_agreement) -> None:
        """User can retrieve their agreement."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/agreements/{signed_agreement.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(signed_agreement.id)
        assert response.data["is_signed"] is True
        assert response.data["is_verified"] is True


@pytest.mark.django_db
class TestAgreementSignAPI:
    def test_sign_agreement(self, user, draft_agreement) -> None:
        """User can sign an agreement."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/agreements/{draft_agreement.id}/sign/",
            {"ip_address": "192.168.1.1"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "signature" in response.data
        assert response.data["agreement"]["status"] == AgreementStatus.SIGNED

    def test_sign_already_signed_fails(self, user, signed_agreement) -> None:
        """Cannot sign an already signed agreement."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/agreements/{signed_agreement.id}/sign/",
            format="json",
        )
        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
class TestAgreementCanonicalAPI:
    def test_get_canonical(self, user, signed_agreement) -> None:
        """User can get canonical JSON."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/agreements/{signed_agreement.id}/canonical/")
        assert response.status_code == status.HTTP_200_OK
        assert "canonical_json" in response.data
        assert "canonical_hash" in response.data


@pytest.mark.django_db
class TestAgreementSignatureAPI:
    def test_get_signature(self, user, signed_agreement) -> None:
        """User can get signature details."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/agreements/{signed_agreement.id}/signature/")
        assert response.status_code == status.HTTP_200_OK
        assert "signature" in response.data
        assert response.data["is_verified"] is True

    def test_get_signature_unsigned_fails(self, user, draft_agreement) -> None:
        """Cannot get signature for unsigned agreement."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/agreements/{draft_agreement.id}/signature/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAgreementExportAPI:
    def test_export_json(self, user, signed_agreement) -> None:
        """User can export agreement as JSON."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/agreements/{signed_agreement.id}/export/",
            {"format": "json"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        assert "attachment" in response["Content-Disposition"]


@pytest.mark.django_db
class TestAgreementVerifyAPI:
    def test_verify_signed_agreement(self, user, signed_agreement) -> None:
        """User can verify a signed agreement."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(f"/api/v1/agreements/{signed_agreement.id}/verify/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_verified"] is True

    def test_verify_unsigned_agreement_fails(self, user, draft_agreement) -> None:
        """Cannot verify an unsigned agreement."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(f"/api/v1/agreements/{draft_agreement.id}/verify/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
