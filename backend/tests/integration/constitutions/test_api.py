"""
Integration tests for Constitution API endpoints.
Source: 05-ROADMAP.md Section 6.5
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.agents.models import Agent
from apps.constitutions.services import (
    activate_version,
    create_constitution,
    create_version,
)
from core.enums import AgentType, ConstitutionStatus

User = get_user_model()


@pytest.fixture
def user() -> Any:
    """Create a test user."""
    return User.objects.create_user(email="user@example.com", password="pass1234")


@pytest.fixture
def agent(user: Any) -> Any:
    """Create a test agent."""
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="Test Agent",
    )


@pytest.fixture
def api_client() -> Any:
    """Return an authenticated API client."""
    from apps.accounts.services.auth import generate_access_token

    client = APIClient()
    return client, generate_access_token


@pytest.mark.django_db
class TestConstitutionListAPI:
    def test_list_constitutions(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can list their constitutions."""
        client, generate_token = api_client
        create_constitution(agent=agent, name="Travel", user=user)
        create_constitution(agent=agent, name="Shopping", user=user)
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/constitutions/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_constitutions_unauthenticated(self, agent: Any, api_client: Any) -> None:
        """Unauthenticated users cannot list constitutions."""
        client, _ = api_client
        response = client.get("/api/v1/constitutions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestConstitutionCreateAPI:
    def test_create_constitution(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can create a constitution."""
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            "/api/v1/constitutions/",
            {
                "agent_id": str(agent.id),
                "name": "Travel Constitution",
                "description": "Rules for travel",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Travel Constitution"
        assert response.data["status"] == "DRAFT"

    def test_create_constitution_for_other_agent_denied(self, user: Any, api_client: Any) -> None:
        """User cannot create constitution for another user's agent."""
        other_user = User.objects.create_user(email="other@example.com", password="pass1234")
        other_agent = Agent.objects.create(
            owner=other_user,
            agent_type=AgentType.USER_AGENT,
            name="Other Agent",
        )
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            "/api/v1/constitutions/",
            {
                "agent_id": str(other_agent.id),
                "name": "Travel",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestConstitutionRetrieveAPI:
    def test_retrieve_constitution(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can retrieve their constitution."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/constitutions/{constitution.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(constitution.id)
        assert response.data["name"] == "Travel"

    def test_retrieve_other_user_constitution_denied(self, user: Any, api_client: Any) -> None:
        """User cannot retrieve another user's constitution."""
        other_user = User.objects.create_user(email="other@example.com", password="pass1234")
        other_agent = Agent.objects.create(
            owner=other_user,
            agent_type=AgentType.USER_AGENT,
            name="Other Agent",
        )
        constitution = create_constitution(agent=other_agent, name="Other", user=other_user)
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/constitutions/{constitution.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestConstitutionActivateAPI:
    def test_activate_version(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can activate a constitution version."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        version = create_version(constitution=constitution, user=user)
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/constitutions/{constitution.id}/activate/",
            {"version_id": str(version.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["constitution"]["status"] == "ACTIVE"

    def test_activate_archives_previous(self, user: Any, agent: Any, api_client: Any) -> None:
        """Activating new version archives previous."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        version1 = create_version(constitution=constitution, user=user)
        activate_version(version=version1, user=user)
        version2 = create_version(constitution=constitution, user=user)
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/constitutions/{constitution.id}/activate/",
            {"version_id": str(version2.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        version1.refresh_from_db()
        assert version1.status == ConstitutionStatus.ARCHIVED


@pytest.mark.django_db
class TestConstitutionVersionsAPI:
    def test_list_versions(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can list versions of their constitution."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        create_version(constitution=constitution, user=user)
        create_version(constitution=constitution, user=user)
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/constitutions/{constitution.id}/versions/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestConstitutionWithRulesAPI:
    def test_create_with_rules(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can create constitution with rules in one call."""
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            "/api/v1/constitutions/with-rules/",
            {
                "agent_id": str(agent.id),
                "name": "Travel",
                "description": "Travel rules",
                "rules": [
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
                        "name": "No phone",
                        "category": "PRIVACY",
                        "field": "phone_number",
                        "operator": "EQUALS",
                        "value": True,
                        "action": "DENY",
                    },
                ],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rules_count"] == 2


@pytest.mark.django_db
class TestPolicyRuleAPI:
    def test_create_rule(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can create a rule."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        version = create_version(constitution=constitution, user=user)
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/constitutions/{constitution.id}/rules/",
            {
                "version_id": str(version.id),
                "rule_number": 1,
                "name": "Max amount",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 700,
                "action": "ALLOW",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rule_number"] == 1

    def test_update_rule(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can update a rule."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        version = create_version(constitution=constitution, user=user)
        from apps.constitutions.services import add_rule

        rule = add_rule(
            version=version,
            rule_number=1,
            name="Old name",
            category="FINANCIAL",
            field="amount",
            operator="LESS_THAN_OR_EQUAL",
            value=700,
            user=user,
        )
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.patch(
            f"/api/v1/rules/{rule.id}/",
            {"name": "New name"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "New name"

    def test_delete_rule(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can delete a rule."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        version = create_version(constitution=constitution, user=user)
        from apps.constitutions.services import add_rule

        rule = add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category="FINANCIAL",
            field="amount",
            operator="LESS_THAN_OR_EQUAL",
            value=700,
            user=user,
        )
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.delete(f"/api/v1/rules/{rule.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_evaluate_rule(self, user: Any, agent: Any, api_client: Any) -> None:
        """User can test a rule against a proposal."""
        constitution = create_constitution(agent=agent, name="Travel", user=user)
        version = create_version(constitution=constitution, user=user)
        from apps.constitutions.services import add_rule

        rule = add_rule(
            version=version,
            rule_number=1,
            name="Max amount",
            category="FINANCIAL",
            field="amount",
            operator="LESS_THAN_OR_EQUAL",
            value=700,
            action="ALLOW",
            user=user,
        )
        client, generate_token = api_client
        token = generate_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/rules/{rule.id}/evaluate/",
            {
                "action": {
                    "action_type": "purchase",
                    "amount": 500.00,
                    "data_fields_requested": [],
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["matches"] is True
