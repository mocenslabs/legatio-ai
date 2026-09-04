"""Agent Service layer.

This module provides a service for managing agents, including creation,
activation, and deactivation, with audit logging.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction

from apps.agents.models import Agent, AgentType
from apps.audit.models import AuditAction
from apps.audit.services import AuditService


class AgentServiceError(Exception):
    """Base exception for agent service errors."""


class AgentService:
    """Service layer for agent operations.

    Manages agent creation and lifecycle (activation/deactivation),
    recording audit events for all changes.
    """

    @staticmethod
    @transaction.atomic
    def create_agent(
        name: str,
        agent_type: str,
        created_by_id: uuid.UUID,
        description: str = "",
        config: dict[str, Any] | None = None,
    ) -> Agent:
        """Create a new agent.

        Args:
            name: Human-readable name for the agent.
            agent_type: The category of agent behavior.
            created_by_id: The UUID of the user creating the agent.
            description: Optional description of the agent's purpose.
            config: Optional JSON configuration for the agent.

        Returns:
            The created Agent instance.

        Raises:
            AgentServiceError: If agent_type is invalid.
        """
        valid_types = {choice.value for choice in AgentType}
        if agent_type not in valid_types:
            raise AgentServiceError(f"Invalid agent_type: {agent_type}")

        agent = Agent.objects.create(
            name=name,
            description=description,
            agent_type=agent_type,
            config=config if config is not None else {},
            created_by_id=created_by_id,
        )

        AuditService.log_agent_event(
            action=AuditAction.AGENT_CREATED,
            agent_id=agent.id,
            actor_id=created_by_id,
            new_state={"name": agent.name, "agent_type": agent.agent_type},
        )

        return agent

    @staticmethod
    @transaction.atomic
    def activate_agent(
        agent_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> Agent:
        """Activate an agent.

        Args:
            agent_id: The UUID of the agent to activate.
            actor_id: Optional UUID of the user activating the agent.

        Returns:
            The updated Agent instance.

        Raises:
            AgentServiceError: If the agent doesn't exist.
        """
        agent = AgentService._get_agent(agent_id)

        if agent.is_active:
            return agent

        agent.is_active = True
        agent.save(update_fields=["is_active", "updated_at"])

        AuditService.log_agent_event(
            action=AuditAction.AGENT_ACTIVATED,
            agent_id=agent.id,
            actor_id=actor_id,
            old_state={"is_active": False},
            new_state={"is_active": True},
        )

        return agent

    @staticmethod
    @transaction.atomic
    def deactivate_agent(
        agent_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> Agent:
        """Deactivate an agent.

        Args:
            agent_id: The UUID of the agent to deactivate.
            actor_id: Optional UUID of the user deactivating the agent.

        Returns:
            The updated Agent instance.

        Raises:
            AgentServiceError: If the agent doesn't exist.
        """
        agent = AgentService._get_agent(agent_id)

        if not agent.is_active:
            return agent

        agent.is_active = False
        agent.save(update_fields=["is_active", "updated_at"])

        AuditService.log_agent_event(
            action=AuditAction.AGENT_DEACTIVATED,
            agent_id=agent.id,
            actor_id=actor_id,
            old_state={"is_active": True},
            new_state={"is_active": False},
        )

        return agent

    @staticmethod
    def _get_agent(agent_id: uuid.UUID) -> Agent:
        """Retrieve an agent or raise an error.

        Args:
            agent_id: The UUID of the agent.

        Returns:
            The Agent instance.

        Raises:
            AgentServiceError: If the agent doesn't exist.
        """
        try:
            return Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist as e:
            raise AgentServiceError(f"Agent {agent_id} not found") from e
