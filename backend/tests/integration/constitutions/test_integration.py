"""
Integration tests for Constitution services with Policy Engine.
"""

from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from core.enums import AgentType, PolicyDecisionOutcome
from core.schemas.policy import ProposedAction
from services.policy_engine.evaluator import evaluate_policy
from services.policy_engine.loader import load_active_rules_for_agent

User = get_user_model()


@pytest.fixture
def user() -> Any:
    """Create a test user."""
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture
def agent(user: Any) -> Any:
    """Create a test agent."""
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="Test Agent",
    )


@pytest.mark.django_db
class TestPolicyEngineIntegration:
    def test_load_rules_from_active_constitution(self, user: Any, agent: Any) -> None:
        """Rules can be loaded from active constitution."""
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
            agent=agent,
            name="Test",
            description=None,
            rules=rules,
            user=user,
        )
        activate_version(version=version, user=user)

        # Load rules
        loaded_rules = load_active_rules_for_agent(agent)
        assert len(loaded_rules) == 1
        assert loaded_rules[0].name == "Max amount"

    def test_evaluate_with_active_constitution(self, user: Any, agent: Any) -> None:
        """Policy Engine can evaluate using active constitution rules."""
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
            {
                "rule_number": 17,
                "name": "Never share phone",
                "category": "PRIVACY",
                "field": "data_fields_requested",
                "operator": "CONTAINS",
                "value": "phone_number",
                "action": "DENY",
            },
        ]

        constitution, version = create_constitution_with_rules(
            agent=agent,
            name="Travel",
            description=None,
            rules=rules,
            user=user,
        )
        activate_version(version=version, user=user)

        # Load rules
        loaded_rules = load_active_rules_for_agent(agent)

        # Test ALLOW
        action1 = ProposedAction(
            action_type="purchase",
            amount=Decimal("500.00"),
            data_fields_requested=[],
        )
        decision1 = evaluate_policy(action1, loaded_rules)
        assert decision1.outcome == PolicyDecisionOutcome.ALLOW

        # Test DENY
        action2 = ProposedAction(
            action_type="purchase",
            amount=Decimal("500.00"),
            data_fields_requested=["phone_number"],
        )
        decision2 = evaluate_policy(action2, loaded_rules)
        assert decision2.outcome == PolicyDecisionOutcome.DENY

    def test_full_madrid_scenario(self, user: Any, agent: Any) -> None:
        """Full Madrid travel scenario works end-to-end."""
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
            agent=agent,
            name="Madrid Travel",
            description=None,
            rules=rules,
            user=user,
        )
        activate_version(version=version, user=user)

        loaded_rules = load_active_rules_for_agent(agent)

        # Round 1: €820 → REQUIRE_APPROVAL
        action1 = ProposedAction(
            action_type="purchase",
            amount=Decimal("820.00"),
            data_fields_requested=[],
        )
        decision1 = evaluate_policy(action1, loaded_rules)
        assert decision1.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

        # Round 2: €680 + phone → DENY
        action2 = ProposedAction(
            action_type="purchase",
            amount=Decimal("680.00"),
            data_fields_requested=["phone_number"],
        )
        decision2 = evaluate_policy(action2, loaded_rules)
        assert decision2.outcome == PolicyDecisionOutcome.DENY

        # Round 3: €700, no phone → REQUIRE_APPROVAL
        action3 = ProposedAction(
            action_type="purchase",
            amount=Decimal("700.00"),
            data_fields_requested=[],
        )
        decision3 = evaluate_policy(action3, loaded_rules)
        assert decision3.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
