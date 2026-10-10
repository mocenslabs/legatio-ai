"""
Unit tests for the SimulatedAgent base interface.
"""

from decimal import Decimal
from typing import Any

import pytest

from core.schemas.policy import ProposedAction
from services.negotiation_engine.base import (
    AgentResponse,
    NegotiationCompletedError,
    SimulatedAgent,
)


class ConcreteTestAgent(SimulatedAgent):
    """Concrete implementation for testing."""

    @property
    def agent_name(self) -> str:
        return "Test Agent"

    @property
    def agent_type(self) -> str:
        return "test"

    def respond(
        self,
        round_number: int,
        user_instruction: str,
        previous_proposals: list[ProposedAction],
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        if round_number != 1:
            raise NegotiationCompletedError("Only 1 round")
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
        )
        return AgentResponse(
            action=action,
            natural_language_summary="Test response",
        )


class TestSimulatedAgentInterface:
    def test_concrete_agent_implements_interface(self) -> None:
        """Concrete agent implements all abstract methods."""
        agent = ConcreteTestAgent()
        assert agent.agent_name == "Test Agent"
        assert agent.agent_type == "test"

    def test_respond_returns_agent_response(self) -> None:
        """respond() returns an AgentResponse."""
        agent = ConcreteTestAgent()
        response = agent.respond(
            round_number=1,
            user_instruction="test",
            previous_proposals=[],
        )
        assert isinstance(response, AgentResponse)
        assert isinstance(response.action, ProposedAction)
        assert response.action.amount == Decimal("100.00")

    def test_negotiation_completed_error(self) -> None:
        """Agent raises NegotiationCompletedError when done."""
        agent = ConcreteTestAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(
                round_number=2,
                user_instruction="test",
                previous_proposals=[],
            )

    def test_reset_is_callable(self) -> None:
        """reset() can be called without error."""
        agent = ConcreteTestAgent()
        agent.reset()  # Should not raise


class TestAgentResponse:
    def test_agent_response_with_metadata(self) -> None:
        """AgentResponse can include metadata."""
        action = ProposedAction(action_type="purchase", amount=Decimal("50"))
        response = AgentResponse(
            action=action,
            natural_language_summary="Test",
            metadata={"key": "value"},
        )
        assert response.metadata == {"key": "value"}

    def test_agent_response_without_metadata(self) -> None:
        """AgentResponse metadata is optional."""
        action = ProposedAction(action_type="purchase")
        response = AgentResponse(
            action=action,
            natural_language_summary="Test",
        )
        assert response.metadata is None
