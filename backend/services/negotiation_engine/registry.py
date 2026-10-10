"""
Registry for simulated agents.

Provides a central place to look up agents by type.
This allows the orchestrator to instantiate the correct agent
based on the negotiation context.

Source: 05-ROADMAP.md Section 7.3
"""

from services.negotiation_engine.base import SimulatedAgent
from services.negotiation_engine.simulated import (
    SimulatedHotelAgent,
    SimulatedISPAgent,
    SimulatedVendorAgent,
)

# Registry mapping agent_type to agent class
AGENT_REGISTRY: dict[str, type[SimulatedAgent]] = {
    "hotel": SimulatedHotelAgent,
    "isp": SimulatedISPAgent,
    "vendor": SimulatedVendorAgent,
}


def get_agent_class(agent_type: str) -> type[SimulatedAgent]:
    """
    Get the agent class for a given agent type.

    Args:
        agent_type: The type of agent (e.g., 'hotel', 'isp', 'vendor', 'SIMULATED').

    Returns:
        The agent class.

    Raises:
        ValueError: If the agent type is not registered.
    """
    # Map SIMULATED to hotel by default (Use Case 1 is the primary scenario)
    if agent_type == "SIMULATED":
        agent_type = "hotel"

    if agent_type not in AGENT_REGISTRY:
        available = ", ".join(sorted(AGENT_REGISTRY.keys()))
        raise ValueError(f"Unknown agent type: '{agent_type}'. Available types: {available}")
    return AGENT_REGISTRY[agent_type]


def create_agent(agent_type: str) -> SimulatedAgent:
    """
    Create an instance of a simulated agent.

    Args:
        agent_type: The type of agent to create.

    Returns:
        A new instance of the agent.
    """
    agent_class = get_agent_class(agent_type)
    return agent_class()


def list_available_agents() -> list[str]:
    """Return a list of all available agent types."""
    return sorted(AGENT_REGISTRY.keys())
