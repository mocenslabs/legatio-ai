"""API tests for Comment, Negotiation, and NegotiationOffer endpoints.

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
from apps.negotiations.models import (
    Comment,
    CommentEntityType,
    Negotiation,
    NegotiationOffer,
    NegotiationStatus,
    OfferStatus,
)
from apps.proposals.models import Proposal


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="user@example.com", password="testpass123")


@pytest.fixture
def other_user(db: None) -> User:
    """Create a second test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="other@example.com", password="testpass123")


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
    """Create a test proposal.

    Args:
        db: The database fixture.
        user: The user fixture.

    Returns:
        A Proposal instance.
    """
    return Proposal.objects.create(
        title="Test Proposal",
        action_type="CREATE_PROPOSAL",
        target_resource="proposals",
        created_by=user,
    )


@pytest.mark.django_db
class TestCommentAPI:
    """Tests for Comment API endpoints."""

    def test_create_comment(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify creating a comment returns 201."""
        url = reverse("comment-list")
        data = {
            "entity_type": "Proposal",
            "entity_id": str(proposal.id),
            "content": "This is a comment",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "This is a comment"
        assert response.data["author"] == user.id
        assert response.data["is_reply"] is False

    def test_create_comment_empty_content_returns_400(
        self, api_client: APIClient, proposal: Proposal
    ) -> None:
        """Verify creating a comment with empty content returns 400."""
        url = reverse("comment-list")
        data = {
            "entity_type": "Proposal",
            "entity_id": str(proposal.id),
            "content": "   ",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_reply(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify creating a reply links to the parent comment."""
        parent = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Parent",
        )

        url = reverse("comment-list")
        data = {
            "entity_type": "Proposal",
            "entity_id": str(proposal.id),
            "content": "Reply",
            "parent": str(parent.id),
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["parent"] == parent.id
        assert response.data["is_reply"] is True

    def test_list_comments(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify listing comments returns paginated results."""
        Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Comment 1",
        )
        Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Comment 2",
        )

        url = reverse("comment-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_by_entity_type(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify filtering comments by entity_type works."""
        Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Proposal comment",
        )
        Comment.objects.create(
            entity_type=CommentEntityType.AGREEMENT,
            entity_id=uuid.uuid4(),
            author=user,
            content="Agreement comment",
        )

        url = reverse("comment-list")
        response = api_client.get(url, {"entity_type": "Proposal"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["entity_type"] == "Proposal"

    def test_retrieve_comment(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify retrieving a single comment works."""
        comment = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Test comment",
        )

        url = reverse("comment-detail", kwargs={"pk": comment.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == "Test comment"

    def test_delete_comment_by_author(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify the author can delete their own comment."""
        comment = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="To delete",
        )

        url = reverse("comment-detail", kwargs={"pk": comment.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_delete_comment_by_non_author_returns_400(
        self, user: User, other_user: User, proposal: Proposal
    ) -> None:
        """Verify a non-author cannot delete a comment."""
        comment = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Protected",
        )

        client = APIClient()
        client.force_authenticate(user=other_user)
        url = reverse("comment-detail", kwargs={"pk": comment.id})
        response = client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Comment.objects.filter(id=comment.id).exists()

    def test_update_comment_not_allowed(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify updating a comment returns 405."""
        comment = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Original",
        )

        url = reverse("comment-detail", kwargs={"pk": comment.id})
        response = api_client.patch(url, {"content": "Modified"}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestNegotiationAPI:
    """Tests for Negotiation API endpoints."""

    def test_create_negotiation(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify creating a negotiation returns 201 and OPEN status."""
        url = reverse("negotiation-list")
        data = {
            "proposal": str(proposal.id),
            "title": "New Negotiation",
            "description": "A test negotiation",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Negotiation"
        assert response.data["status"] == "OPEN"
        assert response.data["initiated_by"] == user.id

    def test_list_negotiations(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify listing negotiations returns paginated results."""
        Negotiation.objects.create(proposal=proposal, title="Neg 1", initiated_by=user)
        Negotiation.objects.create(proposal=proposal, title="Neg 2", initiated_by=user)

        url = reverse("negotiation-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_negotiation_includes_offers(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify retrieving a negotiation includes nested offers."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        NegotiationOffer.objects.create(
            negotiation=negotiation, offered_by=user, terms={"amount": 1000}
        )

        url = reverse("negotiation-detail", kwargs={"pk": negotiation.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "offers" in response.data
        assert len(response.data["offers"]) == 1
        assert "is_active" in response.data

    def test_filter_by_status(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify filtering negotiations by status works."""
        Negotiation.objects.create(
            proposal=proposal, title="Open", initiated_by=user, status=NegotiationStatus.OPEN
        )
        Negotiation.objects.create(
            proposal=proposal, title="Agreed", initiated_by=user, status=NegotiationStatus.AGREED
        )

        url = reverse("negotiation-list")
        response = api_client.get(url, {"status": "OPEN"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "OPEN"

    def test_start_negotiation(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify starting an open negotiation sets status to IN_PROGRESS."""
        negotiation = Negotiation.objects.create(
            proposal=proposal, title="Test", initiated_by=user, status=NegotiationStatus.OPEN
        )

        url = reverse("negotiation-start", kwargs={"pk": negotiation.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "IN_PROGRESS"

    def test_start_non_open_returns_400(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify starting a non-open negotiation returns 400."""
        negotiation = Negotiation.objects.create(
            proposal=proposal, title="Test", initiated_by=user, status=NegotiationStatus.AGREED
        )

        url = reverse("negotiation-start", kwargs={"pk": negotiation.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_make_offer(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify making an offer within a negotiation."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )

        url = reverse("negotiation-make-offer", kwargs={"pk": negotiation.id})
        data = {"terms": {"amount": 5000}, "notes": "Initial offer"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["terms"] == {"amount": 5000}
        assert response.data["round_number"] == 1

    def test_make_offer_on_concluded_returns_400(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify making an offer on a concluded negotiation returns 400."""
        negotiation = Negotiation.objects.create(
            proposal=proposal, title="Test", initiated_by=user, status=NegotiationStatus.AGREED
        )

        url = reverse("negotiation-make-offer", kwargs={"pk": negotiation.id})
        response = api_client.post(url, {"terms": {}}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_conclude_as_failed(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify concluding a negotiation as FAILED."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )

        url = reverse("negotiation-conclude", kwargs={"pk": negotiation.id})
        response = api_client.post(url, {"status": "FAILED"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "FAILED"


@pytest.mark.django_db
class TestNegotiationOfferAPI:
    """Tests for NegotiationOffer API endpoints."""

    def test_list_offers(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify listing offers returns paginated results."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})
        NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        url = reverse("negotiationoffer-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_offer(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify retrieving a single offer works."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(
            negotiation=negotiation, offered_by=user, terms={"amount": 1000}
        )

        url = reverse("negotiationoffer-detail", kwargs={"pk": offer.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["terms"] == {"amount": 1000}
        assert response.data["is_pending"] is True

    def test_filter_by_negotiation(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify filtering offers by negotiation works."""
        negotiation1 = Negotiation.objects.create(
            proposal=proposal, title="Neg 1", initiated_by=user
        )
        negotiation2 = Negotiation.objects.create(
            proposal=proposal, title="Neg 2", initiated_by=user
        )
        NegotiationOffer.objects.create(negotiation=negotiation1, offered_by=user, terms={})
        NegotiationOffer.objects.create(negotiation=negotiation2, offered_by=user, terms={})

        url = reverse("negotiationoffer-list")
        response = api_client.get(url, {"negotiation": str(negotiation1.id)})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_accept_offer(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify accepting an offer sets status to ACCEPTED."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        url = reverse("negotiationoffer-accept", kwargs={"pk": offer.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ACCEPTED"

    def test_reject_offer(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify rejecting an offer sets status to REJECTED."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        url = reverse("negotiationoffer-reject", kwargs={"pk": offer.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "REJECTED"

    def test_withdraw_offer(self, api_client: APIClient, user: User, proposal: Proposal) -> None:
        """Verify withdrawing an offer sets status to WITHDRAWN."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        url = reverse("negotiationoffer-withdraw", kwargs={"pk": offer.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "WITHDRAWN"

    def test_accept_non_pending_returns_400(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify accepting a non-pending offer returns 400."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(
            negotiation=negotiation,
            offered_by=user,
            terms={},
            status=OfferStatus.REJECTED,
        )

        url = reverse("negotiationoffer-accept", kwargs={"pk": offer.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_offer_not_allowed(
        self, api_client: APIClient, user: User, proposal: Proposal
    ) -> None:
        """Verify creating offers directly via API returns 405."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)

        url = reverse("negotiationoffer-list")
        data = {"negotiation": str(negotiation.id), "terms": {}}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestNegotiationAuthentication:
    """Tests for authentication requirements."""

    def test_list_negotiations_unauthenticated_returns_401(
        self, user: User, proposal: Proposal
    ) -> None:
        """Verify unauthenticated requests return 401."""
        Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)

        client = APIClient()
        url = reverse("negotiation-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_comments_unauthenticated_returns_401(
        self, user: User, proposal: Proposal
    ) -> None:
        """Verify unauthenticated requests return 401."""
        Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Test",
        )

        client = APIClient()
        url = reverse("comment-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
