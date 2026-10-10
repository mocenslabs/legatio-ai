"""
Unit tests for the agent registry.
"""

import pytest

from services.negotiation_engine.base import SimulatedAgent
from services.negotiation_engine.registry import (
    AGENT_REGISTRY,
    create_agent,
    get_agent_class,
    list_available_agents,
)
from services.negotiation_engine.simulated import (
    SimulatedHotelAgent,
    SimulatedISPAgent,
    SimulatedVendorAgent,
)


class TestAgentRegistry:
    def test_registry_contains_all_agents(self) -> None:
        """Registry contains all 3 simulated agents."""
        assert "hotel" in AGENT_REGISTRY
        assert "isp" in AGENT_REGISTRY
        assert "vendor" in AGENT_REGISTRY
        assert len(AGENT_REGISTRY) == 3

    def test_get_agent_class_hotel(self) -> None:
        """get_agent_class returns SimulatedHotelAgent for 'hotel'."""
        assert get_agent_class("hotel") is SimulatedHotelAgent

    def test_get_agent_class_isp(self) -> None:
        """get_agent_class returns SimulatedISPAgent for 'isp'."""
        assert get_agent_class("isp") is SimulatedISPAgent

    def test_get_agent_class_vendor(self) -> None:
        """get_agent_class returns SimulatedVendorAgent for 'vendor'."""
        assert get_agent_class("vendor") is SimulatedVendorAgent

    def test_get_agent_class_unknown_raises(self) -> None:
        """get_agent_class raises ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_agent_class("unknown")

    def test_create_agent_returns_instance(self) -> None:
        """create_agent returns a SimulatedAgent instance."""
        agent = create_agent("hotel")
        assert isinstance(agent, SimulatedAgent)
        assert isinstance(agent, SimulatedHotelAgent)

    def test_create_agent_creates_new_instance(self) -> None:
        """create_agent creates a new instance each time."""
        agent1 = create_agent("hotel")
        agent2 = create_agent("hotel")
        assert agent1 is not agent2

    def test_list_available_agents(self) -> None:
        """list_available_agents returns sorted list of types."""
        agents = list_available_agents()
        assert agents == ["hotel", "isp", "vendor"]

    def test_all_registered_agents_are_simulated(self) -> None:
        """All registered agents inherit from SimulatedAgent."""
        for _agent_type, agent_class in AGENT_REGISTRY.items():
            assert issubclass(agent_class, SimulatedAgent)

    def test_all_agents_have_required_properties(self) -> None:
        """All agents have agent_name and agent_type properties."""
        for agent_type in AGENT_REGISTRY:
            agent = create_agent(agent_type)
            assert len(agent.agent_name) > 0
            assert agent.agent_type == agent_type
