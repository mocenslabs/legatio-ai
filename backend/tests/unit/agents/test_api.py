"""API tests for Agent and AutomationRule endpoints.

Tests cover CRUD operations, lifecycle actions, filtering, and
access restrictions.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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
class TestAgentAPI:
    """Tests for Agent API endpoints."""

    def test_create_agent(self, api_client: APIClient, user: User) -> None:
        """Verify creating an agent returns 201 with detail serializer."""
        url = reverse("agent-list")
        data = {
            "name": "New Agent",
            "description": "A test agent",
            "agent_type": "AUTO_PROPOSER",
            "config": {"threshold": 10},
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Agent"
        assert response.data["agent_type"] == "AUTO_PROPOSER"
        assert response.data["is_active"] is True
        assert response.data["created_by"] == user.id
        assert "rules" in response.data

    def test_create_agent_invalid_type_returns_400(self, api_client: APIClient) -> None:
        """Verify creating an agent with invalid type returns 400."""
        url = reverse("agent-list")
        data = {
            "name": "Invalid Agent",
            "agent_type": "INVALID_TYPE",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_agents(self, api_client: APIClient, user: User) -> None:
        """Verify listing agents returns paginated results."""
        Agent.objects.create(name="Agent 1", agent_type=AgentType.MONITOR, created_by=user)
        Agent.objects.create(name="Agent 2", agent_type=AgentType.MONITOR, created_by=user)

        url = reverse("agent-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_agent_includes_rules(
        self, api_client: APIClient, agent: Agent, user: User
    ) -> None:
        """Verify retrieving an agent includes nested rules."""
        AutomationRule.objects.create(
            agent=agent,
            name="Test Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )

        url = reverse("agent-detail", kwargs={"pk": agent.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Agent"
        assert "rules" in response.data
        assert len(response.data["rules"]) == 1
        assert "can_execute" in response.data

    def test_filter_by_agent_type(self, api_client: APIClient, user: User) -> None:
        """Verify filtering agents by type works."""
        Agent.objects.create(name="Proposer", agent_type=AgentType.AUTO_PROPOSER, created_by=user)
        Agent.objects.create(name="Monitor", agent_type=AgentType.MONITOR, created_by=user)

        url = reverse("agent-list")
        response = api_client.get(url, {"agent_type": "MONITOR"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["agent_type"] == "MONITOR"

    def test_filter_by_is_active(self, api_client: APIClient, user: User) -> None:
        """Verify filtering agents by is_active works."""
        Agent.objects.create(
            name="Active", agent_type=AgentType.MONITOR, created_by=user, is_active=True
        )
        Agent.objects.create(
            name="Inactive", agent_type=AgentType.MONITOR, created_by=user, is_active=False
        )

        url = reverse("agent-list")
        response = api_client.get(url, {"is_active": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["is_active"] is True

    def test_activate_agent(self, api_client: APIClient, user: User) -> None:
        """Verify activating an agent sets is_active to True."""
        agent = Agent.objects.create(
            name="Inactive",
            agent_type=AgentType.MONITOR,
            created_by=user,
            is_active=False,
        )

        url = reverse("agent-activate", kwargs={"pk": agent.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is True

    def test_deactivate_agent(self, api_client: APIClient, agent: Agent) -> None:
        """Verify deactivating an agent sets is_active to False."""
        url = reverse("agent-deactivate", kwargs={"pk": agent.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_update_agent(self, api_client: APIClient, agent: Agent) -> None:
        """Verify updating an agent works."""
        url = reverse("agent-detail", kwargs={"pk": agent.id})
        response = api_client.patch(url, {"name": "Updated Name"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_delete_agent(self, api_client: APIClient, agent: Agent) -> None:
        """Verify deleting an agent returns 204."""
        url = reverse("agent-detail", kwargs={"pk": agent.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Agent.objects.filter(id=agent.id).exists()


@pytest.mark.django_db
class TestAutomationRuleAPI:
    """Tests for AutomationRule API endpoints."""

    def test_create_rule(self, api_client: APIClient, agent: Agent, user: User) -> None:
        """Verify creating an automation rule returns 201."""
        url = reverse("automationrule-list")
        data = {
            "agent": str(agent.id),
            "name": "New Rule",
            "trigger_type": "ON_PROPOSAL_CREATED",
            "action_type": "NOTIFY",
            "priority": 50,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Rule"
        assert response.data["agent"] == agent.id
        assert response.data["priority"] == 50

    def test_create_rule_invalid_trigger_returns_400(
        self, api_client: APIClient, agent: Agent
    ) -> None:
        """Verify creating a rule with invalid trigger returns 400."""
        url = reverse("automationrule-list")
        data = {
            "agent": str(agent.id),
            "name": "Invalid Rule",
            "trigger_type": "INVALID_TRIGGER",
            "action_type": "NOTIFY",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_rules(self, api_client: APIClient, agent: Agent, user: User) -> None:
        """Verify listing rules returns paginated results."""
        AutomationRule.objects.create(
            agent=agent,
            name="Rule 1",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )
        AutomationRule.objects.create(
            agent=agent,
            name="Rule 2",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )

        url = reverse("automationrule-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_rule(self, api_client: APIClient, agent: Agent, user: User) -> None:
        """Verify retrieving a single rule works."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Test Rule",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )

        url = reverse("automationrule-detail", kwargs={"pk": rule.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Rule"
        assert "can_fire" in response.data
        assert "has_condition" in response.data

    def test_filter_by_agent(self, api_client: APIClient, user: User) -> None:
        """Verify filtering rules by agent works."""
        agent1 = Agent.objects.create(name="Agent 1", agent_type=AgentType.MONITOR, created_by=user)
        agent2 = Agent.objects.create(name="Agent 2", agent_type=AgentType.MONITOR, created_by=user)
        AutomationRule.objects.create(
            agent=agent1,
            name="Rule 1",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )
        AutomationRule.objects.create(
            agent=agent2,
            name="Rule 2",
            trigger_type=TriggerType.ON_PROPOSAL_CREATED,
            action_type=ActionType.NOTIFY,
            created_by=user,
        )

        url = reverse("automationrule-list")
        response = api_client.get(url, {"agent": str(agent1.id)})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_execute_rule(self, api_client: APIClient, agent: Agent, user: User) -> None:
        """Verify executing a rule returns executed=true."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Executable Rule",
            trigger_type=TriggerType.MANUAL,
            action_type=ActionType.CREATE_PROPOSAL,
            action_config={"title": "Executed Proposal"},
            created_by=user,
            is_active=True,
        )

        url = reverse("automationrule-execute", kwargs={"pk": rule.id})
        response = api_client.post(url, {"context": {}}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["executed"] is True

    def test_execute_rule_condition_not_met(
        self, api_client: APIClient, agent: Agent, user: User
    ) -> None:
        """Verify executing a rule with unmet condition returns executed=false."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Conditional Rule",
            trigger_type=TriggerType.MANUAL,
            action_type=ActionType.CREATE_PROPOSAL,
            condition={"field": "status", "operator": "==", "value": "APPROVED"},
            created_by=user,
            is_active=True,
        )

        url = reverse("automationrule-execute", kwargs={"pk": rule.id})
        response = api_client.post(url, {"context": {"status": "DRAFT"}}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["executed"] is False

    def test_execute_inactive_rule_returns_400(
        self, api_client: APIClient, agent: Agent, user: User
    ) -> None:
        """Verify executing an inactive rule returns 400."""
        rule = AutomationRule.objects.create(
            agent=agent,
            name="Inactive Rule",
            trigger_type=TriggerType.MANUAL,
            action_type=ActionType.CREATE_PROPOSAL,
            created_by=user,
            is_active=False,
        )

        url = reverse("automationrule-execute", kwargs={"pk": rule.id})
        response = api_client.post(url, {"context": {}}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAgentAuthentication:
    """Tests for authentication requirements."""

    def test_list_agents_unauthenticated_returns_401(self, user: User) -> None:
        """Verify unauthenticated requests return 401."""
        Agent.objects.create(name="Test", agent_type=AgentType.MONITOR, created_by=user)

        client = APIClient()
        url = reverse("agent-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
