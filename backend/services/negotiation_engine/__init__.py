"""
Negotiation Engine for Legatio AI.

This module provides the simulated agents and orchestrator that manage
the negotiation lifecycle.

Source: 02-ARCHITECTURE.md Section 8.2
"""

from services.negotiation_engine.base import (
    AgentResponse,
    NegotiationCompletedError,
    SimulatedAgent,
)
from services.negotiation_engine.counter_offers import generate_counter_offer
from services.negotiation_engine.orchestrator import NegotiationOrchestrator
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

__all__ = [
    # Base classes
    "SimulatedAgent",
    "AgentResponse",
    "NegotiationCompletedError",
    # Registry
    "AGENT_REGISTRY",
    "create_agent",
    "get_agent_class",
    "list_available_agents",
    # Simulated agents
    "SimulatedHotelAgent",
    "SimulatedISPAgent",
    "SimulatedVendorAgent",
    # Orchestrator
    "NegotiationOrchestrator",
    # Counter-offers
    "generate_counter_offer",
]
