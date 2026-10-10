"""
State machine for NegotiationRoom.

Defines valid transitions and guards for the negotiation lifecycle.

Source: 04-BUSINESS-FLOW.md Section 8.1 and 8.2
"""

from core.enums import NegotiationStatus
from core.exceptions import NegotiationStateError

# Valid transitions: from_status -> [to_statuses]
VALID_TRANSITIONS: dict[NegotiationStatus, list[NegotiationStatus]] = {
    NegotiationStatus.PENDING: [
        NegotiationStatus.IN_PROGRESS,
        NegotiationStatus.CANCELLED,
    ],
    NegotiationStatus.IN_PROGRESS: [
        NegotiationStatus.AWAITING_APPROVAL,
        NegotiationStatus.FAILED,
        NegotiationStatus.CANCELLED,
    ],
    NegotiationStatus.AWAITING_APPROVAL: [
        NegotiationStatus.COMPLETED,
        NegotiationStatus.CANCELLED,
        NegotiationStatus.EXPIRED,
        NegotiationStatus.FAILED,
    ],
    # Terminal states: no transitions allowed
    NegotiationStatus.COMPLETED: [],
    NegotiationStatus.CANCELLED: [],
    NegotiationStatus.FAILED: [],
    NegotiationStatus.EXPIRED: [],
}

# Terminal states
TERMINAL_STATES = {
    NegotiationStatus.COMPLETED,
    NegotiationStatus.CANCELLED,
    NegotiationStatus.FAILED,
    NegotiationStatus.EXPIRED,
}


def can_transition(
    from_status: NegotiationStatus,
    to_status: NegotiationStatus,
) -> bool:
    """
    Check if a transition between two statuses is valid.

    Args:
        from_status: Current status.
        to_status: Desired status.

    Returns:
        True if the transition is valid, False otherwise.
    """
    valid_targets = VALID_TRANSITIONS.get(from_status, [])
    return to_status in valid_targets


def validate_transition(
    from_status: NegotiationStatus,
    to_status: NegotiationStatus,
) -> None:
    """
    Validate a transition and raise if invalid.

    Args:
        from_status: Current status.
        to_status: Desired status.

    Raises:
        NegotiationStateError: If the transition is invalid.
    """
    if not can_transition(from_status, to_status):
        raise NegotiationStateError(
            f"Invalid transition: {from_status.value} → {to_status.value}. "
            f"Valid targets: {[s.value for s in VALID_TRANSITIONS.get(from_status, [])]}"
        )


def is_terminal(status: NegotiationStatus) -> bool:
    """Check if a status is a terminal state."""
    return status in TERMINAL_STATES
