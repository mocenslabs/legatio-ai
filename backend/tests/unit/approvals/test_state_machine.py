"""
Unit tests for the ApprovalRequest state machine.
Source: 04-BUSINESS-FLOW.md Section 8.3
"""

import pytest

from apps.approvals.state_machine import (
    can_transition,
    is_terminal,
    validate_transition,
)
from core.enums import ApprovalStatus
from core.exceptions import ApprovalStateError


class TestValidTransitions:
    """Tests for valid state transitions."""

    def test_pending_to_approved(self) -> None:
        assert can_transition(ApprovalStatus.PENDING, ApprovalStatus.APPROVED) is True

    def test_pending_to_rejected(self) -> None:
        assert can_transition(ApprovalStatus.PENDING, ApprovalStatus.REJECTED) is True

    def test_pending_to_modified(self) -> None:
        assert can_transition(ApprovalStatus.PENDING, ApprovalStatus.MODIFIED) is True

    def test_pending_to_expired(self) -> None:
        assert can_transition(ApprovalStatus.PENDING, ApprovalStatus.EXPIRED) is True


class TestInvalidTransitions:
    """Tests for invalid state transitions."""

    def test_approved_to_any_invalid(self) -> None:
        for status in ApprovalStatus:
            if status != ApprovalStatus.APPROVED:
                assert can_transition(ApprovalStatus.APPROVED, status) is False

    def test_rejected_to_any_invalid(self) -> None:
        for status in ApprovalStatus:
            if status != ApprovalStatus.REJECTED:
                assert can_transition(ApprovalStatus.REJECTED, status) is False

    def test_modified_to_any_invalid(self) -> None:
        for status in ApprovalStatus:
            if status != ApprovalStatus.MODIFIED:
                assert can_transition(ApprovalStatus.MODIFIED, status) is False

    def test_expired_to_any_invalid(self) -> None:
        for status in ApprovalStatus:
            if status != ApprovalStatus.EXPIRED:
                assert can_transition(ApprovalStatus.EXPIRED, status) is False


class TestValidateTransition:
    def test_valid_transition_passes(self) -> None:
        validate_transition(ApprovalStatus.PENDING, ApprovalStatus.APPROVED)

    def test_invalid_transition_raises(self) -> None:
        with pytest.raises(ApprovalStateError, match="Invalid transition"):
            validate_transition(ApprovalStatus.APPROVED, ApprovalStatus.PENDING)


class TestTerminalStates:
    def test_approved_is_terminal(self) -> None:
        assert is_terminal(ApprovalStatus.APPROVED) is True

    def test_rejected_is_terminal(self) -> None:
        assert is_terminal(ApprovalStatus.REJECTED) is True

    def test_modified_is_terminal(self) -> None:
        assert is_terminal(ApprovalStatus.MODIFIED) is True

    def test_expired_is_terminal(self) -> None:
        assert is_terminal(ApprovalStatus.EXPIRED) is True

    def test_pending_is_not_terminal(self) -> None:
        assert is_terminal(ApprovalStatus.PENDING) is False
