"""API tests for ApprovalRequest endpoints.

Tests cover list, retrieve, resolve action, and access restrictions.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.approvals.models import ApprovalRequest, ApprovalStatus
from apps.proposals.models import Proposal, ProposalStatus


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="approver@example.com", password="testpass123")


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


@pytest.fixture
def proposal(db: None, user: User) -> Proposal:
    """Create a proposal pending approval.

    Args:
        db: The database fixture.
        user: The user fixture.

    Returns:
        A Proposal instance in PENDING_APPROVAL status.
    """
    return Proposal.objects.create(
        title="Pending Proposal",
        action_type="CREATE_PROPOSAL",
        target_resource="proposals",
        created_by=user,
        status=ProposalStatus.PENDING_APPROVAL,
    )


@pytest.mark.django_db
class TestApprovalRequestList:
    """Tests for listing and retrieving approval requests."""

    def test_list_approval_requests(self, api_client: APIClient, proposal: Proposal) -> None:
        """Verify listing approval requests returns paginated results."""
        ApprovalRequest.objects.create(proposal=proposal, required_role="manager")
        ApprovalRequest.objects.create(proposal=proposal, required_role="director")

        url = reverse("approvalrequest-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_approval_request(self, api_client: APIClient, proposal: Proposal) -> None:
        """Verify retrieving a single approval request works."""
        approval = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        url = reverse("approvalrequest-detail", kwargs={"pk": approval.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["required_role"] == "manager"
        assert response.data["status"] == "PENDING"

    def test_filter_by_status(self, api_client: APIClient, proposal: Proposal, user: User) -> None:
        """Verify filtering approval requests by status works."""
        ApprovalRequest.objects.create(proposal=proposal, required_role="manager")
        ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="director",
            status=ApprovalStatus.APPROVED,
            decided_by=user,
        )

        url = reverse("approvalrequest-list")
        response = api_client.get(url, {"status": "PENDING"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "PENDING"

    def test_filter_by_proposal(self, api_client: APIClient, proposal: Proposal) -> None:
        """Verify filtering approval requests by proposal works."""
        ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        url = reverse("approvalrequest-list")
        response = api_client.get(url, {"proposal": str(proposal.id)})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestApprovalRequestResolve:
    """Tests for the resolve action."""

    def test_resolve_approve(self, api_client: APIClient, proposal: Proposal) -> None:
        """Verify approving an approval request updates its status."""
        approval = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        url = reverse("approvalrequest-resolve", kwargs={"pk": approval.id})
        response = api_client.post(url, {"approved": True, "notes": "Looks good"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "APPROVED"
        assert response.data["notes"] == "Looks good"

    def test_resolve_reject(self, api_client: APIClient, proposal: Proposal) -> None:
        """Verify rejecting an approval request updates its status."""
        approval = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        url = reverse("approvalrequest-resolve", kwargs={"pk": approval.id})
        response = api_client.post(url, {"approved": False}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "REJECTED"

    def test_resolve_updates_proposal_status(
        self, api_client: APIClient, proposal: Proposal
    ) -> None:
        """Verify resolving the only approval request approves the proposal."""
        approval = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        url = reverse("approvalrequest-resolve", kwargs={"pk": approval.id})
        api_client.post(url, {"approved": True}, format="json")

        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.APPROVED

    def test_resolve_non_pending_returns_400(
        self, api_client: APIClient, proposal: Proposal, user: User
    ) -> None:
        """Verify resolving a non-pending approval returns 400."""
        approval = ApprovalRequest.objects.create(
            proposal=proposal,
            required_role="manager",
            status=ApprovalStatus.APPROVED,
            decided_by=user,
        )

        url = reverse("approvalrequest-resolve", kwargs={"pk": approval.id})
        response = api_client.post(url, {"approved": True}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestApprovalRequestRestrictions:
    """Tests for access restrictions on approval requests."""

    def test_create_not_allowed(self, api_client: APIClient, proposal: Proposal) -> None:
        """Verify creating approval requests via API returns 405."""
        url = reverse("approvalrequest-list")
        data = {"proposal": str(proposal.id), "required_role": "manager"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, api_client: APIClient, proposal: Proposal) -> None:
        """Verify deleting approval requests via API returns 405."""
        approval = ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        url = reverse("approvalrequest-detail", kwargs={"pk": approval.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_list_unauthenticated_returns_401(self, proposal: Proposal) -> None:
        """Verify unauthenticated requests return 401."""
        ApprovalRequest.objects.create(proposal=proposal, required_role="manager")

        client = APIClient()
        url = reverse("approvalrequest-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
