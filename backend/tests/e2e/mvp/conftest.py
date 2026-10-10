"""Shared fixtures for MVP E2E tests."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.services.auth import generate_access_token
from apps.agents.models import Agent
from core.enums import AgentType

User = get_user_model()


def _extract_results(response):
    """Handle both paginated and non-paginated responses."""
    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]
    return response.data


@pytest.fixture
def e2e_user():
    """Create a test user for E2E tests."""
    return User.objects.create_user(
        email=f"e2e_{id(object())}@example.com",
        password="e2e1234",
        first_name="E2E",
        last_name="User",
    )


@pytest.fixture
def e2e_user_agent(e2e_user):
    """Create user's agent."""
    return Agent.objects.create(
        owner=e2e_user,
        agent_type=AgentType.USER_AGENT,
        name=f"E2E Agent {id(object())}",
    )


@pytest.fixture
def e2e_hotel_agent():
    """Create simulated hotel agent."""
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name=f"Hotel Agent {id(object())}",
    )


@pytest.fixture
def e2e_isp_agent():
    """Create simulated ISP agent."""
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name=f"ISP Agent {id(object())}",
    )


@pytest.fixture
def e2e_vendor_agent():
    """Create simulated vendor agent."""
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name=f"Vendor Agent {id(object())}",
    )


@pytest.fixture
def e2e_auth_client(e2e_user):
    """Create authenticated API client."""
    token = generate_access_token(e2e_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client
