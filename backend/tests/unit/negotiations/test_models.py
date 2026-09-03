"""Unit tests for Comment, Negotiation, and NegotiationOffer models.

Tests cover creation, properties, and string representation.
"""

from __future__ import annotations

import pytest

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
class TestComment:
    """Tests for Comment model."""

    def test_create_minimal(self, user: User, proposal: Proposal) -> None:
        """Verify comment can be created with minimal fields."""
        comment = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="This is a comment",
        )

        assert comment.entity_type == CommentEntityType.PROPOSAL
        assert comment.entity_id == proposal.id
        assert comment.author == user
        assert comment.content == "This is a comment"
        assert comment.parent is None

    def test_create_reply(self, user: User, proposal: Proposal) -> None:
        """Verify a comment can be a reply to another comment."""
        parent = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Parent comment",
        )
        reply = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Reply comment",
            parent=parent,
        )

        assert reply.parent == parent

    def test_is_reply_true(self, user: User, proposal: Proposal) -> None:
        """Verify is_reply returns True when comment has a parent."""
        parent = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Parent",
        )
        reply = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Reply",
            parent=parent,
        )

        assert reply.is_reply is True

    def test_is_reply_false_for_top_level(self, user: User, proposal: Proposal) -> None:
        """Verify is_reply returns False for top-level comments."""
        comment = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Top level",
        )

        assert comment.is_reply is False

    def test_str_representation(self, user: User, proposal: Proposal) -> None:
        """Verify string representation includes author and entity type."""
        comment = Comment.objects.create(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author=user,
            content="Test",
        )

        assert "user@example.com" in str(comment)
        assert "Proposal" in str(comment)


@pytest.mark.django_db
class TestNegotiation:
    """Tests for Negotiation model."""

    def test_create_minimal(self, user: User, proposal: Proposal) -> None:
        """Verify negotiation can be created with minimal fields."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test Negotiation",
            initiated_by=user,
        )

        assert negotiation.proposal == proposal
        assert negotiation.title == "Test Negotiation"
        assert negotiation.status == NegotiationStatus.OPEN
        assert negotiation.initiated_by == user

    def test_default_status_is_open(self, user: User, proposal: Proposal) -> None:
        """Verify default status is OPEN."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
        )

        assert negotiation.status == NegotiationStatus.OPEN

    def test_is_active_true_when_open(self, user: User, proposal: Proposal) -> None:
        """Verify is_active returns True when status is OPEN."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.OPEN,
        )

        assert negotiation.is_active is True

    def test_is_active_true_when_in_progress(self, user: User, proposal: Proposal) -> None:
        """Verify is_active returns True when status is IN_PROGRESS."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )

        assert negotiation.is_active is True

    def test_is_active_false_when_agreed(self, user: User, proposal: Proposal) -> None:
        """Verify is_active returns False when status is AGREED."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.AGREED,
        )

        assert negotiation.is_active is False

    def test_is_concluded_true_when_agreed(self, user: User, proposal: Proposal) -> None:
        """Verify is_concluded returns True when status is AGREED."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.AGREED,
        )

        assert negotiation.is_concluded is True

    def test_is_concluded_false_when_open(self, user: User, proposal: Proposal) -> None:
        """Verify is_concluded returns False when status is OPEN."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.OPEN,
        )

        assert negotiation.is_concluded is False

    def test_str_representation(self, user: User, proposal: Proposal) -> None:
        """Verify string representation includes title and status."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="My Negotiation",
            initiated_by=user,
        )

        assert str(negotiation) == "My Negotiation (OPEN)"


@pytest.mark.django_db
class TestNegotiationOffer:
    """Tests for NegotiationOffer model."""

    def test_create_minimal(self, user: User, proposal: Proposal) -> None:
        """Verify offer can be created with minimal fields."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
        )
        offer = NegotiationOffer.objects.create(
            negotiation=negotiation,
            offered_by=user,
            terms={"amount": 1000},
        )

        assert offer.negotiation == negotiation
        assert offer.offered_by == user
        assert offer.terms == {"amount": 1000}
        assert offer.status == OfferStatus.PENDING
        assert offer.round_number == 1

    def test_default_status_is_pending(self, user: User, proposal: Proposal) -> None:
        """Verify default status is PENDING."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        assert offer.status == OfferStatus.PENDING

    def test_is_pending_true(self, user: User, proposal: Proposal) -> None:
        """Verify is_pending returns True when status is PENDING."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        assert offer.is_pending is True

    def test_is_resolved_true_when_accepted(self, user: User, proposal: Proposal) -> None:
        """Verify is_resolved returns True when status is ACCEPTED."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(
            negotiation=negotiation,
            offered_by=user,
            terms={},
            status=OfferStatus.ACCEPTED,
        )

        assert offer.is_resolved is True

    def test_str_representation(self, user: User, proposal: Proposal) -> None:
        """Verify string representation includes round and status."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(
            negotiation=negotiation, offered_by=user, terms={}, round_number=3
        )

        assert "round 3" in str(offer)
        assert "PENDING" in str(offer)

    def test_cascade_delete_with_negotiation(self, user: User, proposal: Proposal) -> None:
        """Verify offers are deleted when negotiation is deleted."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})
        offer_id = offer.id

        negotiation.delete()

        assert not NegotiationOffer.objects.filter(id=offer_id).exists()
