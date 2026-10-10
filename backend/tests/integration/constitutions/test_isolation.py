"""
Integration tests for Constitution API isolation.
Verifies that users cannot access constitutions of other users.
Source: 00-INDEX.md Section 2.5
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.agents.models import Agent
from apps.constitutions.services import create_constitution, create_version
from core.enums import AgentType

User = get_user_model()


@pytest.fixture
def alice() -> Any:
    """Create Alice."""
    return User.objects.create_user(email="alice@example.com", password="pass1234")


@pytest.fixture
def bob() -> Any:
    """Create Bob."""
    return User.objects.create_user(email="bob@example.com", password="pass1234")


@pytest.fixture
def alice_agent(alice: Any) -> Any:
    """Create Alice's agent."""
    return Agent.objects.create(
        owner=alice,
        agent_type=AgentType.USER_AGENT,
        name="Alice Agent",
    )


@pytest.fixture
def bob_agent(bob: Any) -> Any:
    """Create Bob's agent."""
    return Agent.objects.create(
        owner=bob,
        agent_type=AgentType.USER_AGENT,
        name="Bob Agent",
    )


@pytest.mark.django_db
class TestConstitutionIsolation:
    def test_alice_cannot_see_bob_constitutions(
        self, alice: Any, bob: Any, alice_agent: Any, bob_agent: Any
    ) -> None:
        """Alice cannot list Bob's constitutions."""
        # Created to ensure it exists in DB, but not used directly in assertions
        create_constitution(agent=bob_agent, name="Bob's Constitution", user=bob)
        from apps.accounts.services.auth import generate_access_token

        client = APIClient()
        token = generate_access_token(alice)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/constitutions/")
        assert response.status_code == status.HTTP_200_OK
        # Alice should see 0 constitutions
        assert len(response.data["results"]) == 0

    def test_alice_cannot_retrieve_bob_constitution(
        self, alice: Any, bob: Any, alice_agent: Any, bob_agent: Any
    ) -> None:
        """Alice cannot retrieve Bob's constitution."""
        bob_constitution = create_constitution(agent=bob_agent, name="Bob's Constitution", user=bob)
        from apps.accounts.services.auth import generate_access_token

        client = APIClient()
        token = generate_access_token(alice)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(f"/api/v1/constitutions/{bob_constitution.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_update_bob_constitution(
        self, alice: Any, bob: Any, alice_agent: Any, bob_agent: Any
    ) -> None:
        """Alice cannot update Bob's constitution."""
        bob_constitution = create_constitution(agent=bob_agent, name="Bob's Constitution", user=bob)
        from apps.accounts.services.auth import generate_access_token

        client = APIClient()
        token = generate_access_token(alice)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.patch(
            f"/api/v1/constitutions/{bob_constitution.id}/",
            {"name": "Hacked"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        bob_constitution.refresh_from_db()
        assert bob_constitution.name == "Bob's Constitution"

    def test_alice_cannot_activate_bob_version(
        self, alice: Any, bob: Any, alice_agent: Any, bob_agent: Any
    ) -> None:
        """Alice cannot activate Bob's constitution version."""
        bob_constitution = create_constitution(agent=bob_agent, name="Bob's Constitution", user=bob)
        bob_version = create_version(constitution=bob_constitution, user=bob)
        from apps.accounts.services.auth import generate_access_token

        client = APIClient()
        token = generate_access_token(alice)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/constitutions/{bob_constitution.id}/activate/",
            {"version_id": str(bob_version.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_create_rule_in_bob_version(
        self, alice: Any, bob: Any, alice_agent: Any, bob_agent: Any
    ) -> None:
        """Alice cannot create a rule in Bob's version."""
        bob_constitution = create_constitution(agent=bob_agent, name="Bob's Constitution", user=bob)
        bob_version = create_version(constitution=bob_constitution, user=bob)
        from apps.accounts.services.auth import generate_access_token

        client = APIClient()
        token = generate_access_token(alice)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            f"/api/v1/constitutions/{bob_constitution.id}/rules/",
            {
                "version_id": str(bob_version.id),
                "rule_number": 1,
                "name": "Hacked rule",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "EQUALS",
                "value": 100,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
