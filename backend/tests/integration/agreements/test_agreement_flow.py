"""
Integration tests for the complete agreement flow.
Verifies the full flow from accepted proposal to signed agreement.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.agreements.services import (
    create_agreement_from_proposal,
    sign_agreement,
    verify_agreement_signature,
)
from apps.audit.models import AuditEvent
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import Proposal
from core.enums import (
    AgentType,
    AgreementStatus,
    EventType,
    ProposalStatus,
)

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="flow@example.com", password="pass")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def hotel_agent():
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="Hotel Agent")


@pytest.fixture
def constitution_with_rules(user, user_agent):
    rules = [
        {
            "rule_number": 23,
            "name": "Large payments",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 200,
            "action": "REQUIRE_APPROVAL",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent, name="Rules", description=None, rules=rules, user=user
    )
    activate_version(version=version, user=user)
    return constitution


def _create_accepted_proposal(room, sender, amount="700.00", terms=None):
    """Helper to create an accepted proposal bypassing state machine."""
    if terms is None:
        terms = {"nights": 5, "destination": "Madrid"}
    p = Proposal.objects.create(
        room=room,
        sender=sender,
        action_type="purchase",
        amount=Decimal(amount),
        currency="EUR",
        terms=terms,
        status=ProposalStatus.EVALUATING,
        round_number=3,
    )
    Proposal.objects.filter(id=p.id).update(status=ProposalStatus.ACCEPTED)
    p.refresh_from_db()
    return p


@pytest.mark.django_db
class TestAgreementFlow:
    def test_full_agreement_flow(
        self, user, user_agent, hotel_agent, constitution_with_rules
    ) -> None:
        """Full flow: create agreement from proposal -> sign -> verify."""
        # FIX: Use 'constitution' FK, not 'constitution_version'
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            reference_code="NEG-FLOW-001",
            title="Hotel Madrid",
            user_instruction="Find hotel",
        )
        proposal = _create_accepted_proposal(room, hotel_agent)

        initial_audit_count = AuditEvent.objects.count()

        # 1. Create agreement
        agreement = create_agreement_from_proposal(proposal=proposal, user=user)
        assert agreement.status == AgreementStatus.DRAFT
        assert agreement.canonical_hash is not None

        # 2. Sign agreement
        signature = sign_agreement(
            agreement=agreement,
            user=user,
            ip_address="10.0.0.1",
            user_agent_string="TestClient/1.0",
        )
        assert signature.signature_algorithm == "HMAC-SHA256"

        # 3. Verify signature
        agreement.refresh_from_db()
        assert verify_agreement_signature(agreement) is True

        # 4. Verify audit trail
        assert AuditEvent.objects.count() >= initial_audit_count + 2
        event_types = [e.event_type for e in AuditEvent.objects.all()]
        assert EventType.AGREEMENT_CREATED.value in event_types
        assert EventType.AGREEMENT_SIGNED.value in event_types

    def test_agreement_immutability_after_signing(
        self, user, user_agent, hotel_agent, constitution_with_rules
    ) -> None:
        """Signed agreement cannot be modified."""
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            reference_code="NEG-FLOW-002",
            title="Test",
            user_instruction="Test",
        )
        proposal = _create_accepted_proposal(room, hotel_agent, amount="100.00", terms={})

        agreement = create_agreement_from_proposal(proposal=proposal, user=user)
        sign_agreement(agreement=agreement, user=user)
        agreement.refresh_from_db()
        agreement.status = AgreementStatus.VOIDED
        with pytest.raises(RuntimeError, match="cannot be modified"):
            agreement.save()
