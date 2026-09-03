"""Unit tests for CommentService and NegotiationService.

Tests cover the full lifecycle of comments and negotiations, including
offer exchange and state transitions.
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
from apps.negotiations.services import (
    CommentService,
    CommentServiceError,
    InvalidTransitionError,
    NegotiationService,
    NegotiationServiceError,
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
class TestCommentService:
    """Tests for CommentService class."""

    def test_add_comment(self, user: User, proposal: Proposal) -> None:
        """Verify adding a comment creates it correctly."""
        comment = CommentService.add_comment(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author_id=user.id,
            content="Test comment",
        )

        assert comment.content == "Test comment"
        assert comment.author_id == user.id
        assert comment.entity_id == proposal.id

    def test_add_reply(self, user: User, proposal: Proposal) -> None:
        """Verify adding a reply links to the parent comment."""
        parent = CommentService.add_comment(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author_id=user.id,
            content="Parent",
        )
        reply = CommentService.add_comment(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author_id=user.id,
            content="Reply",
            parent_id=parent.id,
        )

        assert reply.parent_id == parent.id

    def test_add_comment_invalid_entity_type(self, user: User, proposal: Proposal) -> None:
        """Verify adding a comment with invalid entity_type raises error."""
        with pytest.raises(CommentServiceError):
            CommentService.add_comment(
                entity_type="InvalidType",
                entity_id=proposal.id,
                author_id=user.id,
                content="Test",
            )

    def test_add_reply_with_nonexistent_parent(self, user: User, proposal: Proposal) -> None:
        """Verify adding a reply with nonexistent parent raises error."""
        import uuid

        with pytest.raises(CommentServiceError):
            CommentService.add_comment(
                entity_type=CommentEntityType.PROPOSAL,
                entity_id=proposal.id,
                author_id=user.id,
                content="Reply",
                parent_id=uuid.uuid4(),
            )

    def test_delete_comment_by_author(self, user: User, proposal: Proposal) -> None:
        """Verify the author can delete their own comment."""
        comment = CommentService.add_comment(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author_id=user.id,
            content="To delete",
        )

        CommentService.delete_comment(comment.id, actor_id=user.id)

        assert not Comment.objects.filter(id=comment.id).exists()

    def test_delete_comment_by_non_author_raises_error(
        self, user: User, other_user: User, proposal: Proposal
    ) -> None:
        """Verify a non-author cannot delete a comment."""
        comment = CommentService.add_comment(
            entity_type=CommentEntityType.PROPOSAL,
            entity_id=proposal.id,
            author_id=user.id,
            content="Protected",
        )

        with pytest.raises(CommentServiceError):
            CommentService.delete_comment(comment.id, actor_id=other_user.id)


@pytest.mark.django_db
class TestNegotiationServiceCreate:
    """Tests for NegotiationService.create_negotiation."""

    def test_creates_open_negotiation(self, user: User, proposal: Proposal) -> None:
        """Verify negotiation is created in OPEN status."""
        negotiation = NegotiationService.create_negotiation(
            proposal_id=proposal.id,
            title="Test Negotiation",
            description="A test negotiation",
            initiated_by_id=user.id,
        )

        assert negotiation.title == "Test Negotiation"
        assert negotiation.status == NegotiationStatus.OPEN
        assert negotiation.proposal == proposal

    def test_create_with_nonexistent_proposal_raises_error(self, user: User) -> None:
        """Verify creating a negotiation with nonexistent proposal raises error."""
        import uuid

        with pytest.raises(NegotiationServiceError):
            NegotiationService.create_negotiation(
                proposal_id=uuid.uuid4(),
                title="Test",
                description="",
                initiated_by_id=user.id,
            )


@pytest.mark.django_db
class TestNegotiationServiceStart:
    """Tests for NegotiationService.start_negotiation."""

    def test_starts_open_negotiation(self, user: User, proposal: Proposal) -> None:
        """Verify starting an open negotiation sets status to IN_PROGRESS."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.OPEN,
        )

        updated = NegotiationService.start_negotiation(negotiation.id, actor_id=user.id)

        assert updated.status == NegotiationStatus.IN_PROGRESS

    def test_start_non_open_raises_error(self, user: User, proposal: Proposal) -> None:
        """Verify starting a non-open negotiation raises error."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.AGREED,
        )

        with pytest.raises(InvalidTransitionError):
            NegotiationService.start_negotiation(negotiation.id, actor_id=user.id)


@pytest.mark.django_db
class TestNegotiationServiceMakeOffer:
    """Tests for NegotiationService.make_offer."""

    def test_make_offer_assigns_round_number(self, user: User, proposal: Proposal) -> None:
        """Verify making an offer assigns sequential round numbers."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )

        offer1 = NegotiationService.make_offer(
            negotiation_id=negotiation.id,
            offered_by_id=user.id,
            terms={"amount": 1000},
        )
        offer2 = NegotiationService.make_offer(
            negotiation_id=negotiation.id,
            offered_by_id=user.id,
            terms={"amount": 1500},
        )

        assert offer1.round_number == 1
        assert offer2.round_number == 2

    def test_make_offer_on_concluded_raises_error(self, user: User, proposal: Proposal) -> None:
        """Verify making an offer on a concluded negotiation raises error."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.AGREED,
        )

        with pytest.raises(InvalidTransitionError):
            NegotiationService.make_offer(
                negotiation_id=negotiation.id,
                offered_by_id=user.id,
                terms={},
            )


@pytest.mark.django_db
class TestNegotiationServiceAcceptOffer:
    """Tests for NegotiationService.accept_offer."""

    def test_accept_offer_concludes_negotiation(self, user: User, proposal: Proposal) -> None:
        """Verify accepting an offer concludes the negotiation as AGREED."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        NegotiationService.accept_offer(offer.id, actor_id=user.id)

        negotiation.refresh_from_db()
        assert negotiation.status == NegotiationStatus.AGREED

    def test_accept_offer_updates_status(self, user: User, proposal: Proposal) -> None:
        """Verify accepting an offer sets its status to ACCEPTED."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        updated = NegotiationService.accept_offer(offer.id, actor_id=user.id)

        assert updated.status == OfferStatus.ACCEPTED

    def test_accept_non_pending_raises_error(self, user: User, proposal: Proposal) -> None:
        """Verify accepting a non-pending offer raises error."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(
            negotiation=negotiation,
            offered_by=user,
            terms={},
            status=OfferStatus.REJECTED,
        )

        with pytest.raises(InvalidTransitionError):
            NegotiationService.accept_offer(offer.id, actor_id=user.id)


@pytest.mark.django_db
class TestNegotiationServiceWithdrawOffer:
    """Tests for NegotiationService.withdraw_offer."""

    def test_withdraw_own_offer(self, user: User, proposal: Proposal) -> None:
        """Verify the offer creator can withdraw their offer."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        updated = NegotiationService.withdraw_offer(offer.id, actor_id=user.id)

        assert updated.status == OfferStatus.WITHDRAWN

    def test_withdraw_by_non_creator_raises_error(
        self, user: User, other_user: User, proposal: Proposal
    ) -> None:
        """Verify a non-creator cannot withdraw an offer."""
        negotiation = Negotiation.objects.create(proposal=proposal, title="Test", initiated_by=user)
        offer = NegotiationOffer.objects.create(negotiation=negotiation, offered_by=user, terms={})

        with pytest.raises(NegotiationServiceError):
            NegotiationService.withdraw_offer(offer.id, actor_id=other_user.id)


@pytest.mark.django_db
class TestNegotiationServiceConclude:
    """Tests for NegotiationService.conclude_negotiation."""

    def test_conclude_as_failed(self, user: User, proposal: Proposal) -> None:
        """Verify concluding a negotiation as FAILED."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.IN_PROGRESS,
        )

        updated = NegotiationService.conclude_negotiation(
            negotiation_id=negotiation.id,
            target_status=NegotiationStatus.FAILED,
            actor_id=user.id,
        )

        assert updated.status == NegotiationStatus.FAILED

    def test_conclude_already_concluded_raises_error(self, user: User, proposal: Proposal) -> None:
        """Verify concluding an already-concluded negotiation raises error."""
        negotiation = Negotiation.objects.create(
            proposal=proposal,
            title="Test",
            initiated_by=user,
            status=NegotiationStatus.AGREED,
        )

        with pytest.raises(InvalidTransitionError):
            NegotiationService.conclude_negotiation(
                negotiation_id=negotiation.id,
                target_status=NegotiationStatus.FAILED,
                actor_id=user.id,
            )
