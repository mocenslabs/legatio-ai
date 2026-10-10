"""
Base interface for simulated agents.

Defines the contract that all simulated agents must follow.
This interface allows the negotiation orchestrator to interact with
agents uniformly, regardless of whether they are simulated or LLM-based.

Source: 02-ARCHITECTURE.md Section 8.2
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from core.schemas.policy import ProposedAction


@dataclass
class AgentResponse:
    """
    Response from a simulated agent.

    Contains the proposed action and optional metadata.
    """

    action: ProposedAction
    natural_language_summary: str
    metadata: dict[str, Any] | None = None


class SimulatedAgent(ABC):
    """
    Abstract base class for simulated agents.

    All simulated agents must implement the `respond` method,
    which takes the negotiation context and returns a proposed action.
    """

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return the human-readable name of the agent."""
        ...

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return the type of the agent (e.g., 'hotel', 'isp', 'vendor')."""
        ...

    @abstractmethod
    def respond(
        self,
        round_number: int,
        user_instruction: str,
        previous_proposals: list[ProposedAction],
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """
        Generate a response based on the negotiation context.

        Args:
            round_number: The current round of negotiation (1-indexed).
            user_instruction: The original user instruction.
            previous_proposals: List of proposals made so far in the negotiation.
            context: Additional context (e.g., constitution rules, metadata).

        Returns:
            AgentResponse with the proposed action.

        Raises:
            NegotiationCompletedError: If the agent has no more responses
                (negotiation should complete or fail).
        """
        ...

    def reset(self) -> None:
        """Reset the agent's internal state for a new negotiation.

        Default implementation is a no-op. Subclasses that maintain internal
        state (e.g., round counters) SHOULD override this method to reset
        that state, allowing the agent instance to be reused across multiple
        negotiations.
        """
        # No-op by default. Subclasses override when they maintain state.
        return None


class NegotiationCompletedError(Exception):
    """Raised when the simulated agent has no more responses."""

    pass
