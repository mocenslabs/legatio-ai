"""API tests for Agreement and AgreementVersion endpoints.

Tests cover CRUD operations, lifecycle actions, filtering, and
access restrictions.
"""

from __future__ import annotations

import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.agreements.models import Agreement, AgreementStatus, AgreementVersion
from apps.proposals.models import Proposal, ProposalStatus


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="creator@example.com", password="testpass123")


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
class TestAgreementCRUD:
    """Tests for Agreement CRUD operations."""

    def test_create_agreement(self, api_client: APIClient, user: User) -> None:
        """Verify creating an agreement returns 201 and DRAFT status."""
        url = reverse("agreement-list")
        data = {
            "title": "New Agreement",
            "description": "A test agreement",
            "terms": {"clause": "value"},
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Agreement"
        assert response.data["status"] == "DRAFT"
        assert response.data["created_by"] == user.id

    def test_create_agreement_creates_initial_version(self, api_client: APIClient) -> None:
        """Verify creating an agreement also creates version 1."""
        url = reverse("agreement-list")
        data = {
            "title": "New Agreement",
            "terms": {"clause": "value"},
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["versions"]) == 1
        assert response.data["versions"][0]["version_number"] == 1

    def test_list_agreements(self, api_client: APIClient, user: User) -> None:
        """Verify listing agreements returns paginated results."""
        Agreement.objects.create(title="Agreement 1", terms={}, created_by=user)
        Agreement.objects.create(title="Agreement 2", terms={}, created_by=user)

        url = reverse("agreement-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_agreement(self, api_client: APIClient, user: User) -> None:
        """Verify retrieving an agreement includes versions and properties."""
        agreement = Agreement.objects.create(title="Detail Agreement", terms={}, created_by=user)

        url = reverse("agreement-detail", kwargs={"pk": agreement.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Detail Agreement"
        assert "versions" in response.data
        assert "is_active" in response.data
        assert "can_be_activated" in response.data

    def test_filter_by_status(self, api_client: APIClient, user: User) -> None:
        """Verify filtering agreements by status works."""
        Agreement.objects.create(
            title="Draft", terms={}, created_by=user, status=AgreementStatus.DRAFT
        )
        Agreement.objects.create(
            title="Active", terms={}, created_by=user, status=AgreementStatus.ACTIVE
        )

        url = reverse("agreement-list")
        response = api_client.get(url, {"status": "ACTIVE"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "ACTIVE"


@pytest.mark.django_db
class TestAgreementActivate:
    """Tests for the activate action."""

    def test_activate_draft_agreement(self, api_client: APIClient, user: User) -> None:
        """Verify activating a draft agreement sets status to ACTIVE."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
        )

        url = reverse("agreement-activate", kwargs={"pk": agreement.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ACTIVE"
        assert response.data["is_active"] is True

    def test_activate_non_draft_returns_400(self, api_client: APIClient, user: User) -> None:
        """Verify activating a non-draft agreement returns 400."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        url = reverse("agreement-activate", kwargs={"pk": agreement.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAgreementAmend:
    """Tests for the amend action."""

    def test_amend_active_agreement(self, api_client: APIClient, user: User) -> None:
        """Verify amending an active agreement updates terms."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={"version": 1},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )
        AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title=agreement.title,
            terms={"version": 1},
            created_by=user,
        )

        url = reverse("agreement-amend", kwargs={"pk": agreement.id})
        data = {
            "terms": {"version": 2},
            "change_reason": "Updated terms",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["terms"] == {"version": 2}

    def test_amend_creates_new_version(self, api_client: APIClient, user: User) -> None:
        """Verify amending creates a new version."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={"version": 1},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )
        AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title=agreement.title,
            terms={"version": 1},
            created_by=user,
        )

        url = reverse("agreement-amend", kwargs={"pk": agreement.id})
        data = {
            "terms": {"version": 2},
            "change_reason": "Updated terms",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["versions"]) == 2

    def test_amend_non_active_returns_400(self, api_client: APIClient, user: User) -> None:
        """Verify amending a non-active agreement returns 400."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
        )

        url = reverse("agreement-amend", kwargs={"pk": agreement.id})
        data = {
            "terms": {},
            "change_reason": "Test",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAgreementCompleteTerminate:
    """Tests for the complete and terminate actions."""

    def test_complete_active_agreement(self, api_client: APIClient, user: User) -> None:
        """Verify completing an active agreement sets status to COMPLETED."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        url = reverse("agreement-complete", kwargs={"pk": agreement.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "COMPLETED"

    def test_terminate_active_agreement(self, api_client: APIClient, user: User) -> None:
        """Verify terminating an active agreement sets status to TERMINATED."""
        agreement = Agreement.objects.create(
            title="Active Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.ACTIVE,
        )

        url = reverse("agreement-terminate", kwargs={"pk": agreement.id})
        response = api_client.post(url, {"reason": "Breach"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "TERMINATED"

    def test_complete_draft_returns_400(self, api_client: APIClient, user: User) -> None:
        """Verify completing a draft agreement returns 400."""
        agreement = Agreement.objects.create(
            title="Draft Agreement",
            terms={},
            created_by=user,
            status=AgreementStatus.DRAFT,
        )

        url = reverse("agreement-complete", kwargs={"pk": agreement.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGenerateFromProposal:
    """Tests for the generate_from_proposal action."""

    def test_generate_from_executed_proposal(self, api_client: APIClient, user: User) -> None:
        """Verify generating an agreement from an executed proposal."""
        proposal = Proposal.objects.create(
            title="Executed Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            created_by=user,
            status=ProposalStatus.EXECUTED,
        )

        url = reverse("agreement-generate-from-proposal")
        response = api_client.post(url, {"proposal_id": str(proposal.id)}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Executed Proposal"
        assert response.data["terms"] == {"amount": 5000}
        assert response.data["proposal"] == proposal.id

    def test_generate_from_non_executed_returns_400(
        self, api_client: APIClient, user: User
    ) -> None:
        """Verify generating from a non-executed proposal returns 400."""
        proposal = Proposal.objects.create(
            title="Draft Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )

        url = reverse("agreement-generate-from-proposal")
        response = api_client.post(url, {"proposal_id": str(proposal.id)}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_from_nonexistent_returns_400(self, api_client: APIClient) -> None:
        """Verify generating from a nonexistent proposal returns 400."""
        url = reverse("agreement-generate-from-proposal")
        response = api_client.post(url, {"proposal_id": str(uuid.uuid4())}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAgreementVersionAPI:
    """Tests for AgreementVersion API endpoints."""

    def test_list_versions(self, api_client: APIClient, user: User) -> None:
        """Verify listing versions returns paginated results."""
        agreement = Agreement.objects.create(title="Test Agreement", terms={}, created_by=user)
        AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title="V1",
            terms={},
            created_by=user,
        )
        AgreementVersion.objects.create(
            agreement=agreement,
            version_number=2,
            title="V2",
            terms={},
            created_by=user,
        )

        url = reverse("agreementversion-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_version(self, api_client: APIClient, user: User) -> None:
        """Verify retrieving a single version works."""
        agreement = Agreement.objects.create(title="Test Agreement", terms={}, created_by=user)
        version = AgreementVersion.objects.create(
            agreement=agreement,
            version_number=1,
            title="V1",
            terms={"clause": "value"},
            created_by=user,
        )

        url = reverse("agreementversion-detail", kwargs={"pk": version.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["version_number"] == 1
        assert response.data["terms"] == {"clause": "value"}

    def test_filter_by_agreement(self, api_client: APIClient, user: User) -> None:
        """Verify filtering versions by agreement works."""
        agreement1 = Agreement.objects.create(title="Agreement 1", terms={}, created_by=user)
        agreement2 = Agreement.objects.create(title="Agreement 2", terms={}, created_by=user)
        AgreementVersion.objects.create(
            agreement=agreement1, version_number=1, title="V1", terms={}, created_by=user
        )
        AgreementVersion.objects.create(
            agreement=agreement2, version_number=1, title="V1", terms={}, created_by=user
        )

        url = reverse("agreementversion-list")
        response = api_client.get(url, {"agreement": str(agreement1.id)})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_create_version_not_allowed(self, api_client: APIClient, user: User) -> None:
        """Verify creating versions via API returns 405."""
        agreement = Agreement.objects.create(title="Test Agreement", terms={}, created_by=user)

        url = reverse("agreementversion-list")
        data = {
            "agreement": str(agreement.id),
            "version_number": 1,
            "title": "V1",
            "terms": {},
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestAgreementAuthentication:
    """Tests for authentication requirements."""

    def test_list_unauthenticated_returns_401(self, user: User) -> None:
        """Verify unauthenticated requests return 401."""
        Agreement.objects.create(title="Test", terms={}, created_by=user)

        client = APIClient()
        url = reverse("agreement-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
