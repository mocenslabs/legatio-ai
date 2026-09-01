"""API tests for Proposal endpoints.

Tests cover CRUD operations, lifecycle actions, filtering, and authentication.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.policies.models import PolicyRule, RuleActionType
from apps.proposals.models import Proposal, ProposalStatus


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="proposer@example.com", password="testpass123")


@pytest.fixture
def api_client(user: User) -> APIClient:
    """Create an authenticated API client.

    Args:
        user: The user fixture.

    Returns:
        Authenticated APIClient instance.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestProposalCRUD:
    """Tests for Proposal CRUD operations."""

    def test_create_proposal(self, api_client: APIClient) -> None:
        """Verify creating a proposal returns 201 and DRAFT status."""
        url = reverse("proposal-list")
        data = {
            "title": "New Proposal",
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 1000},
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Proposal"
        assert response.data["status"] == "DRAFT"

    def test_create_proposal_sets_created_by(self, api_client: APIClient, user: User) -> None:
        """Verify the authenticated user is set as created_by."""
        url = reverse("proposal-list")
        data = {
            "title": "New Proposal",
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {},
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created_by"] == user.id

    def test_list_proposals(self, api_client: APIClient, user: User) -> None:
        """Verify listing proposals returns paginated results."""
        Proposal.objects.create(
            title="Proposal 1",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )
        Proposal.objects.create(
            title="Proposal 2",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        url = reverse("proposal-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_proposal(self, api_client: APIClient, user: User) -> None:
        """Verify retrieving a proposal returns detail with nested approvals."""
        proposal = Proposal.objects.create(
            title="Detail Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        url = reverse("proposal-detail", kwargs={"pk": proposal.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Detail Proposal"
        assert "approval_requests" in response.data
        assert "requires_approval" in response.data

    def test_filter_by_status(self, api_client: APIClient, user: User) -> None:
        """Verify filtering proposals by status works."""
        Proposal.objects.create(
            title="Draft",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )
        Proposal.objects.create(
            title="Approved",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.APPROVED,
        )

        url = reverse("proposal-list")
        response = api_client.get(url, {"status": "APPROVED"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "APPROVED"


@pytest.mark.django_db
class TestProposalSubmit:
    """Tests for the submit action."""

    def test_submit_allows_when_no_rules(self, api_client: APIClient, user: User) -> None:
        """Verify submitting a draft with no matching rules approves it."""
        proposal = Proposal.objects.create(
            title="Submit Me",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 500},
            created_by=user,
        )

        url = reverse("proposal-submit", kwargs={"pk": proposal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "APPROVED"

    def test_submit_denies_when_deny_rule(self, api_client: APIClient, user: User) -> None:
        """Verify submitting a draft with a matching deny rule denies it."""
        PolicyRule.objects.create(
            name="Deny High Amount",
            condition={"field": "payload.amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
        )
        proposal = Proposal.objects.create(
            title="Submit Me",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            created_by=user,
        )

        url = reverse("proposal-submit", kwargs={"pk": proposal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "DENIED"

    def test_submit_non_draft_returns_400(self, api_client: APIClient, user: User) -> None:
        """Verify submitting a non-draft proposal returns 400."""
        proposal = Proposal.objects.create(
            title="Already Submitted",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.SUBMITTED,
        )

        url = reverse("proposal-submit", kwargs={"pk": proposal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProposalExecute:
    """Tests for the execute action."""

    def test_execute_approved_proposal(self, api_client: APIClient, user: User) -> None:
        """Verify executing an approved proposal transitions to EXECUTED."""
        proposal = Proposal.objects.create(
            title="Execute Me",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.APPROVED,
        )

        url = reverse("proposal-execute", kwargs={"pk": proposal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "EXECUTED"

    def test_execute_draft_returns_400(self, api_client: APIClient, user: User) -> None:
        """Verify executing a draft proposal returns 400."""
        proposal = Proposal.objects.create(
            title="Draft Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )

        url = reverse("proposal-execute", kwargs={"pk": proposal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProposalCancel:
    """Tests for the cancel action."""

    def test_cancel_proposal(self, api_client: APIClient, user: User) -> None:
        """Verify cancelling a proposal transitions to CANCELLED."""
        proposal = Proposal.objects.create(
            title="Cancel Me",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.PENDING_APPROVAL,
        )

        url = reverse("proposal-cancel", kwargs={"pk": proposal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "CANCELLED"


@pytest.mark.django_db
class TestProposalAuthentication:
    """Tests for authentication requirements."""

    def test_list_unauthenticated_returns_401(self, user: User) -> None:
        """Verify unauthenticated requests return 401."""
        Proposal.objects.create(
            title="Test",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
        )

        client = APIClient()
        url = reverse("proposal-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
