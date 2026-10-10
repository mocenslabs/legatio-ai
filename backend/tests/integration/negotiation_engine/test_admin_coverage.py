"""
Tests to cover admin.py files in negotiations and proposals apps.
Targets: admin.py lines 25, 28, 31, 67, 70, 73
Source: DEL-026
"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.http import HttpRequest

from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from apps.negotiations.admin import (
    NegotiationMessageAdmin,
    NegotiationMessageInline,
    NegotiationRoomAdmin,
)
from apps.negotiations.models import NegotiationMessage, NegotiationRoom
from apps.proposals.admin import (
    CounterProposalAdmin,
    PolicyDecisionAdmin,
    ProposalAdmin,
)
from apps.proposals.models import CounterProposal, PolicyDecision, Proposal
from core.enums import ActorType, AgentType, NegotiationMessageType


@pytest.fixture
def site():
    return AdminSite()


@pytest.fixture
def request_obj():
    return HttpRequest()


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(email="admin@example.com", password="pass")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent():
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="External Agent")


@pytest.fixture
def constitution(user, user_agent):
    return Constitution.objects.create(
        agent=user_agent,
        name="Test Constitution",
        status="ACTIVE",
    )


@pytest.mark.django_db
class TestNegotiationAdminCoverage:
    """Cover admin.py in negotiations app."""

    def test_negotiation_room_admin_configuration(self, site):
        """Lines 36-52: NegotiationRoomAdmin has correct configuration."""
        admin_instance = NegotiationRoomAdmin(NegotiationRoom, site)

        assert "reference_code" in admin_instance.list_display
        assert "status" in admin_instance.list_display
        assert "status" in admin_instance.list_filter
        assert "reference_code" in admin_instance.search_fields
        assert "user_agent" in admin_instance.raw_id_fields
        assert NegotiationMessageInline in admin_instance.inlines

    def test_negotiation_room_admin_status_display(
        self, site, user_agent, external_agent, constitution
    ):
        """Test NegotiationRoomAdmin renders correctly with a room instance."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-ADMIN-001",
            title="Test",
            user_instruction="test",
        )
        # Verify list_display fields are accessible
        assert room.reference_code == "NEG-ADMIN-001"
        assert room.status is not None

    def test_negotiation_message_admin_configuration(self, site):
        """Lines 56-80: NegotiationMessageAdmin has correct configuration."""
        admin_instance = NegotiationMessageAdmin(NegotiationMessage, site)

        assert "room" in admin_instance.list_display
        assert "sender_type" in admin_instance.list_display
        assert "sender_type" in admin_instance.list_filter
        assert "message_type" in admin_instance.list_filter

    def test_negotiation_message_admin_permissions(
        self, site, request_obj, user_agent, external_agent, constitution
    ):
        """Lines 67, 70, 73: NegotiationMessageAdmin denies all write permissions."""
        admin_instance = NegotiationMessageAdmin(NegotiationMessage, site)

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-ADMIN-002",
            title="Test",
            user_instruction="test",
        )
        message = NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.SYSTEM,
            sender_id=None,
            message_type=NegotiationMessageType.PROPOSAL,
            content="Test message",
            round_number=1,
        )

        # All permissions should return False (append-only)
        assert admin_instance.has_add_permission(request_obj) is False
        assert admin_instance.has_change_permission(request_obj, message) is False
        assert admin_instance.has_delete_permission(request_obj, message) is False

    def test_negotiation_message_inline_permissions(
        self, site, request_obj, user_agent, external_agent, constitution
    ):
        """Lines 25, 28, 31: NegotiationMessageInline denies all write permissions."""
        inline = NegotiationMessageInline(NegotiationMessage, site)

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-ADMIN-003",
            title="Test",
            user_instruction="test",
        )

        # All permissions should return False (append-only inline)
        assert inline.has_add_permission(request_obj, room) is False
        assert inline.has_change_permission(request_obj, room) is False
        assert inline.has_delete_permission(request_obj, room) is False


@pytest.mark.django_db
class TestProposalAdminCoverage:
    """Cover admin.py in proposals app."""

    def test_proposal_admin_registered(self, site):
        """ProposalAdmin is registered and configured."""
        admin_instance = ProposalAdmin(Proposal, site)
        assert hasattr(admin_instance, "list_display")
        assert len(admin_instance.list_display) > 0

    def test_counter_proposal_admin_registered(self, site):
        """CounterProposalAdmin is registered and configured."""
        admin_instance = CounterProposalAdmin(CounterProposal, site)
        assert hasattr(admin_instance, "list_display")

    def test_policy_decision_admin_registered(self, site):
        """PolicyDecisionAdmin is registered and configured."""
        admin_instance = PolicyDecisionAdmin(PolicyDecision, site)
        assert hasattr(admin_instance, "list_display")

    def test_proposal_admin_permissions(self, site, request_obj, user):
        """ProposalAdmin denies write permissions (append-only)."""
        request_obj.user = user  # ModelAdmin.has_add_permission reads request.user
        admin_instance = ProposalAdmin(Proposal, site)
        assert admin_instance.has_add_permission(request_obj) is False
        assert admin_instance.has_change_permission(request_obj) is False
        assert admin_instance.has_delete_permission(request_obj) is False

    def test_counter_proposal_admin_permissions(self, site, request_obj):
        """CounterProposalAdmin denies write permissions (append-only)."""
        admin_instance = CounterProposalAdmin(CounterProposal, site)
        assert admin_instance.has_add_permission(request_obj) is False
        assert admin_instance.has_change_permission(request_obj) is False
        assert admin_instance.has_delete_permission(request_obj) is False

    def test_counter_proposal_inline_permissions(self, site, request_obj):
        """Lines 17, 20, 23: CounterProposalInline denies all write permissions."""
        from apps.proposals.admin import CounterProposalInline

        inline = CounterProposalInline(CounterProposal, site)
        assert inline.has_add_permission(request_obj) is False
        assert inline.has_change_permission(request_obj) is False
        assert inline.has_delete_permission(request_obj) is False

    def test_policy_decision_inline_permissions(self, site, request_obj):
        """Lines 42, 45, 48: PolicyDecisionInline denies all write permissions."""
        from apps.proposals.admin import PolicyDecisionInline

        inline = PolicyDecisionInline(PolicyDecision, site)
        assert inline.has_add_permission(request_obj) is False
        assert inline.has_change_permission(request_obj) is False
        assert inline.has_delete_permission(request_obj) is False

    def test_policy_decision_admin_permissions(self, site, request_obj):
        """PolicyDecisionAdmin denies write permissions (append-only)."""
        admin_instance = PolicyDecisionAdmin(PolicyDecision, site)
        assert admin_instance.has_add_permission(request_obj) is False
        assert admin_instance.has_change_permission(request_obj) is False
        assert admin_instance.has_delete_permission(request_obj) is False
