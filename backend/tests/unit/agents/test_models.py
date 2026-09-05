"""Unit tests for Agent and AutomationRule models.

Tests cover creation, properties, constraints, and string representation.
"""

from __future__ import annotations

import pytest

from apps.accounts.models import User
from apps.agents.models import (
    ActionType,
    Agent,
    AgentType,
    AutomationRule,
    TriggerType,
)


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
def agent(db: None, user: User) -> Agent:
    """Create a test agent.

    Args:
        db: The database fixture.
        user: The user fixture.

    Returns:
        An Agent instance.
    """
    return Agent.objects.create(
        name="Test Agent",
        agent_type=AgentType.AUTO_PROPOSER,
        created_by=user,
    )


@pytest.mark.django_db
class TestAgent:
    """Tests for Agent model."""

    def test_create_minimal(self, user: User) -> None:
        """Verify agent can be created with minimal fields."""
        agent = Agent.objects.create(
            name="Minimal Agent",
            agent_type=AgentType.MONITOR,
            created_by=user,
        )

        assert agent.name == "Minimal Agent"
        assert agent.agent_type == AgentType.MONITOR
        assert agent.is_active is True
        assert agent.config == {}
        assert agent.description == ""

    def test_create_with_all_fields(self, user: User) -> None:
        """Verify agent can be created with all fields."""
        config = {"key": "value", "threshold": 10}
        agent = Agent.objects.create(
            name="Full Agent",
            description="A fully configured agent",
            agent_type=AgentType.AUTO_APPROVER,
            config=config,
            is_active=False,
            created_by=user,
        )

        assert agent.name == "Full Agent"
        assert agent.description == "A fully configured agent"
        assert agent.agent_type == AgentType.AUTO_APPROVER
        assert agent.config == config
        assert agent.is_active is False

    def test_str_representation(self, user: User) -> None:
        """Verify string representation includes name and type."""
        agent = Agent.objects.create(
            name="My Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
        )

        assert str(agent) == "My Agent (AUTO_PROPOSER)"

    def test_can_execute_true_when_active(self, user: User) -> None:
        """Verify can_execute returns True when agent is active."""
        agent = Agent.objects.create(
            name="Active Agent",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=True,
        )

        assert agent.can_execute is True

    def test_can_execute_false_when_inactive(self, user: User) -> None:
        """Verify can_execute returns False when agent is inactive."""
        agent = Agent.objects.create(
            name="Inactive Agent",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=False,
        )

        assert agent.can_execute is False

    def test_ordering_by_created_at_desc(self, user: User) -> None:
        """Verify agents are ordered by created_at descending."""
        agent1 = Agent.objects.create(name="First", agent_type=AgentType.MONITOR, created_by=user)
        agent2 = Agent.objects.create(name="Second", agent_type=AgentType.MONITOR, created_by=user)

        agents = list(Agent.objects.all())

        assert agents[0].id == agent2.id
        assert agents[1].id == agent1.id


@pytest.mark.django_db
class TestAutomationRule:
    """Tests for AutomationRule model."""

    def test_create_minimal(self, agent: Agent, user: User) -> None:
        """Verify automation rule can be created with minimal fields."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Test Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )

        assert rule.name == "Test Rule"
        assert rule.trigger_type == TriggerType.ON_PROPOSAL_CREATED
        assert rule.action_type == ActionType.NOTIFY
        assert rule.priority == 100
        assert rule.is_active is True
        assert rule.condition == {}
        assert rule.action_config == {}

    def test_create_with_condition_and_config(self, agent: Agent, user: User) -> None:
        """Verify rule can be created with condition and action config."""
        condition = {"field": "status", "operator": "==", "value": "DRAFT"}
        action_config = {"title": "Automated notification"}
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Configured Rule",
            trigger_type=TriggerType.ON_PROPOSAL_SUBMITTED,
            action_type=ActionType.ADD_COMMENT,
            condition=condition,
            action_config=action_config,
            priority=10,
            created_by=user,
        )

        assert rule.condition == condition
        assert rule.action_config == action_config
        assert rule.priority == 10

    def test_str_representation(self, agent: Agent, user: User) -> None:
        """Verify string representation includes trigger and action."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="My Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            created_by=user,
        )

        assert "My Rule" in str(rule)
        assert "ON_PROPOSAL_CREATED" in str(rule)
        assert "CREATE_PROPOSAL" in str(rule)

    def test_can_fire_true_when_both_active(self, agent: Agent, user: User) -> None:
        """Verify can_fire returns True when rule and agent are active."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Active Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
            is_active=True,
        )

        assert rule.can_fire is True

    def test_can_fire_false_when_rule_inactive(self, agent: Agent, user: User) -> None:
        """Verify can_fire returns False when rule is inactive."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Inactive Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
            is_active=False,
        )

        assert rule.can_fire is False

    def test_can_fire_false_when_agent_inactive(self, user: User) -> None:
        """Verify can_fire returns False when agent is inactive."""
        inactive_agent = Agent.objects.create(
            name="Inactive Agent",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=False,
        )
        rule = AutomationRule.objects.create(
            agent=inactive_agent,
            name="Active Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
            is_active=True,
        )

        assert rule.can_fire is False

    def test_has_condition_true(self, agent: Agent, user: User) -> None:
        """Verify has_condition returns True when condition is set."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Conditional Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            condition={"field": "status", "operator": "==", "value": "DRAFT"},
            created_by=user,
        )

        assert rule.has_condition is True

    def test_has_condition_false_when_empty(self, agent: Agent, user: User) -> None:
        """Verify has_condition returns False when condition is empty."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Unconditional Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )

        assert rule.has_condition is False

    def test_cascade_delete_with_agent(self, agent: Agent, user: User) -> None:
        """Verify rules are deleted when agent is deleted."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Test Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )
        rule_id = rule.id

        agent.delete()

        assert not AutomationRule.objects.filter(id=rule_id).exists()

    def test_ordering_by_priority(self, agent: Agent, user: User) -> None:
        """Verify rules are ordered by priority ascending."""
        rule1 = AutomationRule.objects.create(
            agent=agent,
            name="High Priority",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            priority=1,
            created_by=user,
        )
        rule2 = AutomationRule.objects.create(
            agent=agent,
            name="Low Priority",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            priority=100,
            created_by=user,
        )

        rules = list(AutomationRule.objects.all())

        assert rules[0].id == rule1.id
        assert rules[1].id == rule2.id
