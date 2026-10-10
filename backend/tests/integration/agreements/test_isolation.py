"""
Integration tests for Agreement API isolation.

Verifies that users cannot access agreements of other users.
Source: 00-INDEX.md Section 2.5
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services.auth import generate_access_token
from apps.agents.models import Agent
from apps.agreements.services import create_agreement_from_proposal, sign_agreement
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
def alice():
    """Create Alice."""
    return User.objects.create_user(email="alice@example.com", password="pass1234")


@pytest.fixture
def bob():
    """Create Bob."""
    return User.objects.create_user(email="bob@example.com", password="pass1234")


@pytest.fixture
def alice_agent(alice):
    """Create Alice's agent."""
    return Agent.objects.create(
        owner=alice,
        agent_type=AgentType.USER_AGENT,
        name="Alice Agent",
    )


@pytest.fixture
def bob_agent(bob):
    """Create Bob's agent."""
    return Agent.objects.create(
        owner=bob,
        agent_type=AgentType.USER_AGENT,
        name="Bob Agent",
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
def alice_constitution(alice, alice_agent):
    """Create Alice's constitution."""
    const = Constitution.objects.create(
        agent=alice_agent, name="Alice Rules", status=ConstitutionStatus.ACTIVE
    )
    version = ConstitutionVersion.objects.create(
        constitution=const, version_number=1, created_by=alice
    )
    activate_version(version=version, user=alice)
    return const


@pytest.fixture
def bob_constitution(bob, bob_agent):
    """Create Bob's constitution."""
    const = Constitution.objects.create(
        agent=bob_agent, name="Bob Rules", status=ConstitutionStatus.ACTIVE
    )
    version = ConstitutionVersion.objects.create(
        constitution=const, version_number=1, created_by=bob
    )
    activate_version(version=version, user=bob)
    return const


@pytest.fixture
def bob_agreement(bob, bob_agent, external_agent, bob_constitution):
    """Create Bob's agreement (signed)."""
    room = NegotiationRoom.objects.create(
        user_agent=bob_agent,
        external_agent=external_agent,
        constitution=bob_constitution,
        reference_code="NEG-BOB-001",
        title="Bob's Negotiation",
        user_instruction="Test",
    )
    p = Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("700.00"),
        currency="EUR",
        status=ProposalStatus.EVALUATING,
        round_number=1,
    )
    Proposal.objects.filter(id=p.id).update(status=ProposalStatus.ACCEPTED)
    p.refresh_from_db()
    agreement = create_agreement_from_proposal(proposal=p, user=bob)
    sign_agreement(agreement=agreement, user=bob)
    agreement.refresh_from_db()
    return agreement


@pytest.mark.django_db
class TestAgreementIsolation:
    def test_alice_cannot_see_bob_agreements(self, alice, bob, bob_agreement) -> None:
        """Alice cannot list Bob's agreements."""
        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/agreements/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        if isinstance(data, dict) and "results" in data:
            data = data["results"]
        assert len(data) == 0

    def test_alice_cannot_retrieve_bob_agreement(self, alice, bob, bob_agreement) -> None:
        """Alice cannot retrieve Bob's agreement."""
        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/agreements/{bob_agreement.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_sign_bob_agreement(self, alice, bob, bob_agreement) -> None:
        """Alice cannot sign Bob's agreement."""
        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(f"/api/v1/agreements/{bob_agreement.id}/sign/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_get_bob_canonical(self, alice, bob, bob_agreement) -> None:
        """Alice cannot get Bob's canonical JSON."""
        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/agreements/{bob_agreement.id}/canonical/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_export_bob_agreement(self, alice, bob, bob_agreement) -> None:
        """Alice cannot export Bob's agreement."""
        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/agreements/{bob_agreement.id}/export/",
            {"format": "json"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_verify_bob_agreement(self, alice, bob, bob_agreement) -> None:
        """Alice cannot verify Bob's agreement."""
        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(f"/api/v1/agreements/{bob_agreement.id}/verify/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
