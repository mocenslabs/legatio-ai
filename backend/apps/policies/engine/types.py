"""Core domain types and data structures for the Policy Engine.

This module defines the fundamental dataclasses and enumerations used to
represent actions, decisions, and their outcomes within the deterministic
policy evaluation process.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class DecisionOutcome(str, Enum):
    """Possible outcomes of a policy evaluation."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"
    ERROR = "ERROR"


class RiskLevel(str, Enum):
    """Risk levels associated with actions and decisions."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(tz=UTC)


@dataclass(frozen=True)
class ProposedAction:
    """Represents an action proposed by an actor within the system.

    Attributes:
        action_type: The type of action being proposed (e.g., 'CREATE_PROPOSAL').
        target_resource: The resource or entity the action targets.
        payload: Arbitrary data associated with the action.
        actor_id: The UUID of the user or agent proposing the action.
    """

    action_type: str
    target_resource: str
    payload: dict[str, Any]
    actor_id: uuid.UUID


@dataclass(frozen=True)
class PolicyDecision:
    """The deterministic result of evaluating a ProposedAction against policies.

    Attributes:
        outcome: The final decision outcome.
        risk_level: The assessed risk level of the action.
        reason: A human-readable explanation for the decision.
        matched_rules: List of PolicyRule UUIDs that influenced the decision.
        requires_approval_from: List of roles or user UUIDs required for approval.
        timestamp: The exact time the decision was made (UTC).
    """

    outcome: DecisionOutcome
    risk_level: RiskLevel
    reason: str
    matched_rules: list[uuid.UUID] = field(default_factory=list)
    requires_approval_from: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_utc_now)
