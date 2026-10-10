"""
Unit tests for the Agent model.

Source: 03-DATA-MODEL.md Section 7.1
"""

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from core.enums import AgentStatus, AgentType

User = get_user_model()


@pytest.mark.django_db
class TestAgentModel:
    """Tests for the Agent model."""

    def test_create_user_agent(self) -> None:
        """User agent can be created."""
        user = User.objects.create_user(email="user@example.com", password="pass")
        agent = Agent.objects.create(
            owner=user,
            agent_type=AgentType.USER_AGENT,
            name="My Travel Agent",
        )
        assert agent.owner == user
        assert agent.agent_type == AgentType.USER_AGENT
        assert agent.status == AgentStatus.ACTIVE
        assert agent.deleted_at is None

    def test_create_external_agent(self) -> None:
        """External agent can be created without owner."""
        agent = Agent.objects.create(
            owner=None,
            agent_type=AgentType.EXTERNAL_AGENT,
            name="Hotel Agent",
            external_endpoint_url="https://hotel.example.com/api",
        )
        assert agent.owner is None
        assert agent.agent_type == AgentType.EXTERNAL_AGENT
        assert agent.external_endpoint_url == "https://hotel.example.com/api"

    def test_create_simulated_agent(self) -> None:
        """Simulated agent can be created."""
        agent = Agent.objects.create(
            agent_type=AgentType.SIMULATED,
            name="Test Hotel",
        )
        assert agent.agent_type == AgentType.SIMULATED

    def test_agent_id_is_uuid(self) -> None:
        """Agent ID is a UUID."""
        agent = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="Test",
        )
        import uuid as uuid_module

        assert isinstance(agent.id, uuid_module.UUID)

    def test_soft_delete(self) -> None:
        """Agent can be soft-deleted."""
        agent = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="Test",
        )
        agent.soft_delete()
        agent.refresh_from_db()
        assert agent.deleted_at is not None
        assert agent.is_deleted is True

    def test_soft_delete_excludes_from_default_manager(self) -> None:
        """Soft-deleted agents are excluded from default manager."""
        agent1 = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="Active",
        )
        agent2 = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="Deleted",
        )
        agent2.soft_delete()

        # Default manager excludes deleted
        assert Agent.objects.count() == 1
        assert Agent.objects.first() == agent1

        # all_objects includes deleted
        assert Agent.all_objects.count() == 2

    def test_restore_soft_deleted(self) -> None:
        """Soft-deleted agent can be restored."""
        agent = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="Test",
        )
        agent.soft_delete()
        assert Agent.objects.count() == 0

        agent.restore()
        assert Agent.objects.count() == 1
        assert agent.is_deleted is False

    def test_capabilities_default_empty_list(self) -> None:
        """Capabilities default to empty list."""
        agent = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="Test",
        )
        assert agent.capabilities == []

    def test_protocol_version_default(self) -> None:
        """Protocol version defaults to '1.0'."""
        agent = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="Test",
        )
        assert agent.protocol_version == "1.0"

    def test_str_representation(self) -> None:
        """String representation includes name and type."""
        agent = Agent.objects.create(
            agent_type=AgentType.USER_AGENT,
            name="My Agent",
        )
        assert "My Agent" in str(agent)
        assert "User Agent" in str(agent)

    def test_cascade_delete_with_user(self) -> None:
        """Deleting user deletes their agents."""
        user = User.objects.create_user(email="user@example.com", password="pass")
        agent = Agent.objects.create(
            owner=user,
            agent_type=AgentType.USER_AGENT,
            name="Test",
        )
        agent_id = agent.id
        user.delete()
        assert not Agent.all_objects.filter(id=agent_id).exists()
