"""Unit tests for AgentService and AutomationService.

Tests cover agent lifecycle, rule creation, trigger processing,
and rule execution.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from apps.accounts.models import User
from apps.agents.models import (
    ActionType,
    Agent,
    AgentType,
    AutomationRule,
    TriggerType,
)
from apps.agents.services import (
    AgentService,
    AgentServiceError,
    AutomationService,
    AutomationServiceError,
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
    return User.objects.create_user(email="creator@example.com", password="testpass123")


@pytest.mark.django_db
class TestAgentServiceCreate:
    """Tests for AgentService.create_agent."""

    def test_creates_agent(self, user: User) -> None:
        """Verify agent is created correctly."""
        agent = AgentService.create_agent(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by_id=user.id,
            description="A test agent",
            config={"key": "value"},
        )

        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.AUTO_PROPOSER
        assert agent.is_active is True
        assert agent.config == {"key": "value"}

    def test_create_invalid_agent_type_raises_error(self, user: User) -> None:
        """Verify creating an agent with invalid type raises error."""
        with pytest.raises(AgentServiceError):
            AgentService.create_agent(
                name="Test",
                agent_type="INVALID_TYPE",
                created_by_id=user.id,
            )


@pytest.mark.django_db
class TestAgentServiceActivate:
    """Tests for AgentService.activate_agent."""

    def test_activates_inactive_agent(self, user: User) -> None:
        """Verify activating an inactive agent sets is_active to True."""
        agent = Agent.objects.create(
            name="Inactive",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=False,
        )

        updated = AgentService.activate_agent(agent.id, actor_id=user.id)

        assert updated.is_active is True

    def test_activate_active_agent_is_idempotent(self, user: User) -> None:
        """Verify activating an already-active agent is idempotent."""
        agent = Agent.objects.create(
            name="Active",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=True,
        )

        updated = AgentService.activate_agent(agent.id, actor_id=user.id)

        assert updated.is_active is True

    def test_activate_nonexistent_raises_error(self, user: User) -> None:
        """Verify activating a nonexistent agent raises error."""
        with pytest.raises(AgentServiceError):
            AgentService.activate_agent(uuid.uuid4(), actor_id=user.id)


@pytest.mark.django_db
class TestAgentServiceDeactivate:
    """Tests for AgentService.deactivate_agent."""

    def test_deactivates_active_agent(self, user: User) -> None:
        """Verify deactivating an active agent sets is_active to False."""
        agent = Agent.objects.create(
            name="Active",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=True,
        )

        updated = AgentService.deactivate_agent(agent.id, actor_id=user.id)

        assert updated.is_active is False

    def test_deactivate_inactive_agent_is_idempotent(self, user: User) -> None:
        """Verify deactivating an already-inactive agent is idempotent."""
        agent = Agent.objects.create(
            name="Inactive",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=False,
        )

        updated = AgentService.deactivate_agent(agent.id, actor_id=user.id)

        assert updated.is_active is False


@pytest.mark.django_db
class TestAutomationServiceCreateRule:
    """Tests for AutomationService.create_rule."""

    def test_creates_rule(self, user: User) -> None:
        """Verify rule is created correctly."""
        agent = Agent.objects.create(
            name="Test Agent", agent_type=AgentType.AUTO_PROPOSER, created_by=user
        )

        rule = AutomationService.create_rule(
            agent_id=agent.id,
            name="Test Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by_id=user.id,
            condition={"field": "status", "operator": "==", "value": "DRAFT"},
            action_config={"title": "Automated"},
            priority=50,
        )

        assert rule.name == "Test Rule"
        assert rule.agent == agent
        assert rule.priority == 50
        assert rule.condition == {"field": "status", "operator": "==", "value": "DRAFT"}

    def test_create_invalid_trigger_raises_error(self, user: User) -> None:
        """Verify creating a rule with invalid trigger raises error."""
        agent = Agent.objects.create(
            name="Test Agent", agent_type=AgentType.MONITOR, created_by=user
        )

        with pytest.raises(AutomationServiceError):
            AutomationService.create_rule(
                agent_id=agent.id,
                name="Test",
                trigger_type="INVALID_TRIGGER",
                action_type=ActionType.NOTIFY,
                created_by_id=user.id,
            )

    def test_create_invalid_action_raises_error(self, user: User) -> None:
        """Verify creating a rule with invalid action raises error."""
        agent = Agent.objects.create(
            name="Test Agent", agent_type=AgentType.MONITOR, created_by=user
        )

        with pytest.raises(AutomationServiceError):
            AutomationService.create_rule(
                agent_id=agent.id,
                name="Test",
                trigger_type=TriggerType.ON_PROPOSAL_CREATED,
                action_type="INVALID_ACTION",
                created_by_id=user.id,
            )

    def test_create_with_nonexistent_agent_raises_error(self, user: User) -> None:
        """Verify creating a rule with nonexistent agent raises error."""
        with pytest.raises(AutomationServiceError):
            AutomationService.create_rule(
                agent_id=uuid.uuid4(),
                name="Test",
                trigger_type=TriggerType.ON_PROPOSAL_CREATED,
                action_type=ActionType.NOTIFY,
                created_by_id=user.id,
            )


@pytest.mark.django_db
class TestAutomationServiceProcessTrigger:
    """Tests for AutomationService.process_trigger."""

    def test_executes_matching_rule(self, user: User) -> None:
        """Verify matching active rules are executed."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Create Proposal Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            action_config={"title": "Automated Proposal", "action_type": "AUTO"},
            created_by=user,
            is_active=True,
        )

        executed = AutomationService.process_trigger(
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            context={},
        )

        assert len(executed) == 1
        assert Proposal.objects.filter(title="Automated Proposal").exists()

    def test_skips_inactive_rule(self, user: User) -> None:
        """Verify inactive rules are skipped."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Inactive Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            created_by=user,
            is_active=False,
        )

        executed = AutomationService.process_trigger(
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            context={},
        )

        assert len(executed) == 0

    def test_skips_rule_when_agent_inactive(self, user: User) -> None:
        """Verify rules are skipped when agent is inactive."""
        agent = Agent.objects.create(
            name="Inactive Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=False,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Active Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            created_by=user,
            is_active=True,
        )

        executed = AutomationService.process_trigger(
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            context={},
        )

        assert len(executed) == 0

    def test_executes_when_condition_met(self, user: User) -> None:
        """Verify rule executes when condition is met."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Conditional Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            condition={"field": "status", "operator": "==", "value": "DRAFT"},
            action_config={"title": "Conditional Proposal"},
            created_by=user,
            is_active=True,
        )

        executed = AutomationService.process_trigger(
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            context={"status": "DRAFT"},
        )

        assert len(executed) == 1
        assert Proposal.objects.filter(title="Conditional Proposal").exists()

    def test_skips_when_condition_not_met(self, user: User) -> None:
        """Verify rule is skipped when condition is not met."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Conditional Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            condition={"field": "status", "operator": "==", "value": "APPROVED"},
            created_by=user,
            is_active=True,
        )

        executed = AutomationService.process_trigger(
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            context={"status": "DRAFT"},
        )

        assert len(executed) == 0

    def test_fail_safe_continues_on_error(self, user: User) -> None:
        """Verify processing continues when a rule fails."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Failing Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            priority=1,
            created_by=user,
            is_active=True,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Successful Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.CREATE_PROPOSAL,
            action_config={"title": "Successful Proposal"},
            priority=2,
            created_by=user,
            is_active=True,
        )

        # Patch _execute_rule_action to raise on first call
        call_count = {"value": 0}
        original_execute = AutomationService._execute_rule_action

        def failing_execute(rule: AutomationRule, context: dict) -> None:
            call_count["value"] += 1
            if call_count["value"] == 1:
                raise RuntimeError("Simulated failure")
            original_execute(rule, context)

        with patch.object(AutomationService, "_execute_rule_action", side_effect=failing_execute):
            executed = AutomationService.process_trigger(
                trigger_type=TriggerType.ON_PROPOSAL_CREATED,
                context={},
            )

        # Only the second rule should have executed successfully
        assert len(executed) == 1
        assert Proposal.objects.filter(title="Successful Proposal").exists()


@pytest.mark.django_db
class TestAutomationServiceExecuteRule:
    """Tests for AutomationService.execute_rule."""

    def test_executes_rule(self, user: User) -> None:
        """Verify executing a rule returns True and performs action."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Test Rule",
            trigger_type=TriggerType.MANUAL,
            action_type=ActionType.CREATE_PROPOSAL,
            action_config={"title": "Manual Proposal"},
            created_by=user,
            is_active=True,
        )

        executed = AutomationService.execute_rule(rule.id, context={})

        assert executed is True
        assert Proposal.objects.filter(title="Manual Proposal").exists()

    def test_condition_not_met_returns_false(self, user: User) -> None:
        """Verify execute_rule returns False when condition is not met."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Conditional Rule",
            trigger_type=TriggerType.MANUAL,
            action_type=ActionType.CREATE_PROPOSAL,
            condition={"field": "status", "operator": "==", "value": "APPROVED"},
            created_by=user,
            is_active=True,
        )

        executed = AutomationService.execute_rule(rule.id, context={"status": "DRAFT"})

        assert executed is False

    def test_execute_nonexistent_raises_error(self, user: User) -> None:
        """Verify executing a nonexistent rule raises error."""
        with pytest.raises(AutomationServiceError):
            AutomationService.execute_rule(uuid.uuid4(), context={})

    def test_execute_inactive_rule_raises_error(self, user: User) -> None:
        """Verify executing an inactive rule raises error."""
        agent = Agent.objects.create(
            name="Test Agent",
            agent_type=AgentType.AUTO_PROPOSER,
            created_by=user,
            is_active=True,
        )
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Inactive Rule",
            trigger_type=TriggerType.MANUAL,
            action_type=ActionType.CREATE_PROPOSAL,
            created_by=user,
            is_active=False,
        )

        with pytest.raises(AutomationServiceError):
            AutomationService.execute_rule(rule.id, context={})
