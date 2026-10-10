"""
State machine for Proposal.

Defines valid transitions and guards for the proposal lifecycle.

Source: 04-BUSINESS-FLOW.md Section 8.2
"""

from core.enums import ProposalStatus
from core.exceptions import ProposalStateError

# Valid transitions: from_status -> [to_statuses]
VALID_TRANSITIONS: dict[ProposalStatus, list[ProposalStatus]] = {
    ProposalStatus.RECEIVED: [
        ProposalStatus.EVALUATING,
    ],
    ProposalStatus.EVALUATING: [
        ProposalStatus.ALLOWED,
        ProposalStatus.DENIED,
        ProposalStatus.PENDING_APPROVAL,
    ],
    ProposalStatus.ALLOWED: [
        ProposalStatus.ACCEPTED,
        ProposalStatus.REJECTED,
    ],
    ProposalStatus.DENIED: [
        ProposalStatus.SUPERSEDED,
    ],
    ProposalStatus.PENDING_APPROVAL: [
        ProposalStatus.ACCEPTED,
        ProposalStatus.REJECTED,
        ProposalStatus.EXPIRED,
    ],
    ProposalStatus.ACCEPTED: [
        ProposalStatus.SUPERSEDED,
    ],
    # Terminal states: no transitions allowed
    ProposalStatus.REJECTED: [],
    ProposalStatus.SUPERSEDED: [],
    ProposalStatus.EXPIRED: [],
}

# Terminal states
TERMINAL_STATES = {
    ProposalStatus.REJECTED,
    ProposalStatus.SUPERSEDED,
    ProposalStatus.EXPIRED,
}


def can_transition(
    from_status: ProposalStatus,
    to_status: ProposalStatus,
) -> bool:
    """Check if a transition between two statuses is valid."""
    valid_targets = VALID_TRANSITIONS.get(from_status, [])
    return to_status in valid_targets


def validate_transition(
    from_status: ProposalStatus,
    to_status: ProposalStatus,
) -> None:
    """
    Validate a transition and raise if invalid.

    Raises:
        ProposalStateError: If the transition is invalid.
    """
    if not can_transition(from_status, to_status):
        raise ProposalStateError(
            f"Invalid transition: {from_status.value} → {to_status.value}. "
            f"Valid targets: {[s.value for s in VALID_TRANSITIONS.get(from_status, [])]}"
        )


def is_terminal(status: ProposalStatus) -> bool:
    """Check if a status is a terminal state."""
    return status in TERMINAL_STATES
