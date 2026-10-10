"""
State machine for ApprovalRequest.

Defines valid transitions and guards for the approval lifecycle.

Source: 04-BUSINESS-FLOW.md Section 8.3
"""

from core.enums import ApprovalStatus
from core.exceptions import ApprovalStateError

# Valid transitions: from_status -> [to_statuses]
VALID_TRANSITIONS: dict[ApprovalStatus, list[ApprovalStatus]] = {
    ApprovalStatus.PENDING: [
        ApprovalStatus.APPROVED,
        ApprovalStatus.REJECTED,
        ApprovalStatus.MODIFIED,
        ApprovalStatus.EXPIRED,
    ],
    # Terminal states: no transitions allowed
    ApprovalStatus.APPROVED: [],
    ApprovalStatus.REJECTED: [],
    ApprovalStatus.MODIFIED: [],
    ApprovalStatus.EXPIRED: [],
}

# Terminal states
TERMINAL_STATES = {
    ApprovalStatus.APPROVED,
    ApprovalStatus.REJECTED,
    ApprovalStatus.MODIFIED,
    ApprovalStatus.EXPIRED,
}


def can_transition(
    from_status: ApprovalStatus,
    to_status: ApprovalStatus,
) -> bool:
    """Check if a transition between two statuses is valid."""
    valid_targets = VALID_TRANSITIONS.get(from_status, [])
    return to_status in valid_targets


def validate_transition(
    from_status: ApprovalStatus,
    to_status: ApprovalStatus,
) -> None:
    """
    Validate a transition and raise if invalid.

    Raises:
        ApprovalStateError: If the transition is invalid.
    """
    if not can_transition(from_status, to_status):
        raise ApprovalStateError(
            f"Invalid transition: {from_status.value} → {to_status.value}. "
            f"Valid targets: {[s.value for s in VALID_TRANSITIONS.get(from_status, [])]}"
        )


def is_terminal(status: ApprovalStatus) -> bool:
    """Check if a status is a terminal state."""
    return status in TERMINAL_STATES
