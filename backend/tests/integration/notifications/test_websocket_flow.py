"""Integration tests for WebSocket notification flow."""

from decimal import Decimal
from typing import Any

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from apps.accounts.services.auth import generate_access_token
from apps.agents.models import Agent
from apps.approvals.services import create_approval_request
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.negotiations.models import NegotiationRoom
from apps.notifications.consumers import NotificationConsumer
from apps.notifications.middleware import JWTAuthMiddleware
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    AgentType,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)

User = get_user_model()


@pytest.fixture
def channel_layer_settings(settings: Any) -> Any:
    """Use InMemoryChannelLayer for tests."""
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    return settings


@pytest.fixture
def application(channel_layer_settings: Any) -> Any:
    """Build ASGI application with JWT middleware."""
    return JWTAuthMiddleware(NotificationConsumer.as_asgi())


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="ws_flow@example.com", password="testpass123")


@pytest.fixture
def user_agent(user: Any) -> Any:
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent() -> Any:
    return Agent.objects.create(owner=None, agent_type=AgentType.EXTERNAL_AGENT, name="Hotel Agent")


@pytest.fixture
def constitution_with_rules(user: Any, user_agent: Any) -> Any:
    rules = [
        {
            "rule_number": 23,
            "name": "Large payments require approval",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 200,
            "action": "REQUIRE_APPROVAL",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent,
        name="Test Rules",
        description="Rules for WebSocket flow test",
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.fixture
def room(user_agent: Any, external_agent: Any, constitution_with_rules: Any) -> Any:
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution_with_rules,
        reference_code="NEG-WS-001",
        title="Test Negotiation",
        user_instruction="Test instruction",
    )


@pytest.fixture
def proposal(room: Any, external_agent: Any) -> Any:
    return Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("820.00"),
        currency="EUR",
        round_number=1,
        status=ProposalStatus.EVALUATING,
    )


@pytest.fixture
def policy_decision(proposal: Any, constitution_with_rules: Any) -> Any:
    return PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=constitution_with_rules.active_version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.MEDIUM,
        reason="Amount €820 exceeds auto-approve limit of €200",
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebSocketApprovalFlow:
    async def test_approval_required_notification_sent(
        self, application: Any, user: Any, room: Any, proposal: Any, policy_decision: Any
    ) -> None:
        """WebSocket notification is sent when approval is created."""
        token = await sync_to_async(generate_access_token)(user)

        communicator = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        connected, _ = await communicator.connect()
        assert connected

        # Receive connection.established
        await communicator.receive_json_from()

        # Create approval request (triggers WebSocket notification)
        await sync_to_async(create_approval_request)(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )

        # Should receive approval.required event
        response = await communicator.receive_json_from(timeout=5)
        assert response["type"] == "approval.required"
        assert "approval_id" in response["payload"]
        assert "summary" in response["payload"]
        assert response["payload"]["summary"].startswith("⚠️ Approval Required")

        await communicator.disconnect()
