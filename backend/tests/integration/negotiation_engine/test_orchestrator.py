"""
Integration tests for the NegotiationOrchestrator.
Verifies the complete negotiation lifecycle.
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.audit.models import AuditEvent
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.proposals.models import CounterProposal
from core.enums import (
    AgentType,
    NegotiationStatus,
)
from core.exceptions import NegotiationStateError
from services.negotiation_engine.orchestrator import NegotiationOrchestrator

User = get_user_model()


@pytest.fixture()
def user() -> Any:
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture()
def user_agent(user: Any) -> Any:
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="User Agent",
    )


@pytest.fixture()
def hotel_agent() -> Any:
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name="Hotel Agent",
    )


@pytest.fixture()
def constitution_with_rules(user: Any, user_agent: Any) -> Any:
    rules = [
        {
            "rule_number": 1,
            "name": "Max transaction",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 700,
            "action": "ALLOW",
        },
        {
            "rule_number": 17,
            "name": "Never share phone",
            "category": "PRIVACY",
            "field": "data_fields_requested",
            "operator": "CONTAINS",
            "value": "phone_number",
            "action": "DENY",
        },
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
        agent=user_agent,
        name="Travel Rules",
        description=None,
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.mark.django_db()
class TestNegotiationOrchestrator:
    def test_create_room(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        constitution_with_rules: Any,
    ) -> None:
        """NegotiationRoom can be created."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        assert room.status == NegotiationStatus.PENDING
        assert room.user_agent == user_agent
        assert room.external_agent == hotel_agent
        assert "NEG-" in room.reference_code

    def test_start_negotiation(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        constitution_with_rules: Any,
    ) -> None:
        """Negotiation can be started."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        room.refresh_from_db()
        assert room.status == NegotiationStatus.IN_PROGRESS

    def test_process_round_creates_proposal(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        constitution_with_rules: Any,
    ) -> None:
        """Processing a round creates a Proposal."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        result = orchestrator.process_round()
        assert "proposal" in result
        assert "policy_decision" in result
        assert "outcome" in result
        assert result["proposal"].round_number == 1

    def test_deny_generates_counter_offer(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        constitution_with_rules: Any,
    ) -> None:
        """DENY outcome generates a counter-offer."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        result = orchestrator.process_round()
        if result["outcome"] == "DENY":
            assert result["counter_offer"] is not None
            assert isinstance(result["counter_offer"], CounterProposal)

    def test_audit_events_created(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        constitution_with_rules: Any,
    ) -> None:
        """Audit events are created during negotiation."""
        initial_count = AuditEvent.objects.count()
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()
        assert AuditEvent.objects.count() >= initial_count + 3

    def test_max_rounds_protection(
        self,
        user: Any,
        user_agent: Any,
        hotel_agent: Any,
        constitution_with_rules: Any,
    ) -> None:
        """Max rounds protection prevents infinite loops."""
        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution_with_rules,
            title="Hotel Madrid",
            user_instruction="Find hotel in Madrid",
            max_rounds=2,
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()
        orchestrator.process_round()
        with pytest.raises(NegotiationStateError, match="Max rounds exceeded"):
            orchestrator.process_round()
        room.refresh_from_db()
        assert room.status == NegotiationStatus.FAILED
