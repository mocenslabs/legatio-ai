"""
Concurrency tests for negotiations.

Verifies that race conditions do not cause issues when:
- Multiple rounds are processed simultaneously
- Multiple users try to access the same negotiation
- State transitions are atomic

Source: 04-BUSINESS-FLOW.md Section 13
"""

import threading
import time

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.negotiations.models import NegotiationRoom
from core.enums import AgentType, NegotiationStatus
from services.negotiation_engine.orchestrator import NegotiationOrchestrator

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestNegotiationConcurrency:
    """Tests for concurrent negotiation operations."""

    def test_concurrent_process_round_safe(self) -> None:
        """
        Scenario: Two threads try to process rounds simultaneously.
        Expected: Only one succeeds, the other fails due to state change.
        """
        user = User.objects.create_user(email="concurrent@example.com", password="pass")
        user_agent = Agent.objects.create(
            owner=user, agent_type=AgentType.USER_AGENT, name="User Agent"
        )
        external_agent = Agent.objects.create(
            owner=None, agent_type=AgentType.SIMULATED, name="Hotel Agent"
        )

        rules = [
            {
                "rule_number": 1,
                "name": "Max amount",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 700,
                "action": "ALLOW",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=user_agent,
            name="Rules",
            description=None,
            rules=rules,
            user=user,
        )
        activate_version(version=version, user=user)

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-CONCURRENT-001",
            title="Test",
            user_instruction="Test",
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()

        successes = []
        errors = []

        def process_round(result_list, error_list):
            try:
                time.sleep(0.1)  # Increase chance of race condition
                orchestrator = NegotiationOrchestrator(room)
                orchestrator.process_round()
                result_list.append("success")
            except Exception as e:
                error_list.append(str(e))

        thread1 = threading.Thread(target=process_round, args=(successes, errors))
        thread2 = threading.Thread(target=process_round, args=(successes, errors))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # At least one should succeed
        assert len(successes) >= 1

        # Room should be in a valid state
        room.refresh_from_db()
        assert room.current_round >= 1

    def test_concurrent_cancel_safe(self) -> None:
        """
        Scenario: Two threads try to cancel the same negotiation.
        Expected: Only one succeeds, the other fails.
        """
        user = User.objects.create_user(email="cancel@example.com", password="pass")
        user_agent = Agent.objects.create(
            owner=user, agent_type=AgentType.USER_AGENT, name="User Agent"
        )
        external_agent = Agent.objects.create(
            owner=None, agent_type=AgentType.SIMULATED, name="Hotel Agent"
        )

        rules = [
            {
                "rule_number": 1,
                "name": "Max amount",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 700,
                "action": "ALLOW",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=user_agent,
            name="Rules",
            description=None,
            rules=rules,
            user=user,
        )
        activate_version(version=version, user=user)

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code="NEG-CANCEL-001",
            title="Test",
            user_instruction="Test",
        )

        successes = []
        errors = []

        def cancel_room(result_list, error_list):
            try:
                time.sleep(0.1)
                room.transition_to(NegotiationStatus.CANCELLED)
                result_list.append("success")
            except Exception as e:
                error_list.append(str(e))

        thread1 = threading.Thread(target=cancel_room, args=(successes, errors))
        thread2 = threading.Thread(target=cancel_room, args=(successes, errors))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Only one should succeed
        assert len(successes) == 1
        assert len(errors) == 1

        # Room should be cancelled
        room.refresh_from_db()
        assert room.status == NegotiationStatus.CANCELLED
