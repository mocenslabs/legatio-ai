"""
Unit tests for the NegotiationRoom state machine.

Source: 04-BUSINESS-FLOW.md Section 8.1 and 8.2
"""

import pytest

from apps.negotiations.state_machine import (
    can_transition,
    is_terminal,
    validate_transition,
)
from core.enums import NegotiationStatus
from core.exceptions import NegotiationStateError


class TestValidTransitions:
    """Tests for valid state transitions."""

    def test_pending_to_in_progress(self) -> None:
        assert can_transition(NegotiationStatus.PENDING, NegotiationStatus.IN_PROGRESS) is True

    def test_pending_to_cancelled(self) -> None:
        assert can_transition(NegotiationStatus.PENDING, NegotiationStatus.CANCELLED) is True

    def test_in_progress_to_awaiting_approval(self) -> None:
        assert (
            can_transition(NegotiationStatus.IN_PROGRESS, NegotiationStatus.AWAITING_APPROVAL)
            is True
        )

    def test_in_progress_to_failed(self) -> None:
        assert can_transition(NegotiationStatus.IN_PROGRESS, NegotiationStatus.FAILED) is True

    def test_in_progress_to_cancelled(self) -> None:
        assert can_transition(NegotiationStatus.IN_PROGRESS, NegotiationStatus.CANCELLED) is True

    def test_awaiting_approval_to_completed(self) -> None:
        assert (
            can_transition(NegotiationStatus.AWAITING_APPROVAL, NegotiationStatus.COMPLETED) is True
        )

    def test_awaiting_approval_to_cancelled(self) -> None:
        assert (
            can_transition(NegotiationStatus.AWAITING_APPROVAL, NegotiationStatus.CANCELLED) is True
        )

    def test_awaiting_approval_to_expired(self) -> None:
        assert (
            can_transition(NegotiationStatus.AWAITING_APPROVAL, NegotiationStatus.EXPIRED) is True
        )


class TestInvalidTransitions:
    """Tests for invalid state transitions."""

    def test_pending_to_completed_invalid(self) -> None:
        assert can_transition(NegotiationStatus.PENDING, NegotiationStatus.COMPLETED) is False

    def test_pending_to_awaiting_approval_invalid(self) -> None:
        assert (
            can_transition(NegotiationStatus.PENDING, NegotiationStatus.AWAITING_APPROVAL) is False
        )

    def test_in_progress_to_completed_invalid(self) -> None:
        assert can_transition(NegotiationStatus.IN_PROGRESS, NegotiationStatus.COMPLETED) is False

    def test_completed_to_any_invalid(self) -> None:
        for status in NegotiationStatus:
            if status != NegotiationStatus.COMPLETED:
                assert can_transition(NegotiationStatus.COMPLETED, status) is False

    def test_cancelled_to_any_invalid(self) -> None:
        for status in NegotiationStatus:
            if status != NegotiationStatus.CANCELLED:
                assert can_transition(NegotiationStatus.CANCELLED, status) is False

    def test_failed_to_any_invalid(self) -> None:
        for status in NegotiationStatus:
            if status != NegotiationStatus.FAILED:
                assert can_transition(NegotiationStatus.FAILED, status) is False

    def test_expired_to_any_invalid(self) -> None:
        for status in NegotiationStatus:
            if status != NegotiationStatus.EXPIRED:
                assert can_transition(NegotiationStatus.EXPIRED, status) is False


class TestValidateTransition:
    def test_valid_transition_passes(self) -> None:
        validate_transition(NegotiationStatus.PENDING, NegotiationStatus.IN_PROGRESS)

    def test_invalid_transition_raises(self) -> None:
        with pytest.raises(NegotiationStateError, match="Invalid transition"):
            validate_transition(NegotiationStatus.COMPLETED, NegotiationStatus.PENDING)


class TestTerminalStates:
    def test_completed_is_terminal(self) -> None:
        assert is_terminal(NegotiationStatus.COMPLETED) is True

    def test_cancelled_is_terminal(self) -> None:
        assert is_terminal(NegotiationStatus.CANCELLED) is True

    def test_failed_is_terminal(self) -> None:
        assert is_terminal(NegotiationStatus.FAILED) is True

    def test_expired_is_terminal(self) -> None:
        assert is_terminal(NegotiationStatus.EXPIRED) is True

    def test_pending_is_not_terminal(self) -> None:
        assert is_terminal(NegotiationStatus.PENDING) is False

    def test_in_progress_is_not_terminal(self) -> None:
        assert is_terminal(NegotiationStatus.IN_PROGRESS) is False

    def test_awaiting_approval_is_not_terminal(self) -> None:
        assert is_terminal(NegotiationStatus.AWAITING_APPROVAL) is False


class TestFullLifecycle:
    """Test the full happy-path lifecycle."""

    def test_happy_path(self) -> None:
        """PENDING → IN_PROGRESS → AWAITING_APPROVAL → COMPLETED."""
        transitions = [
            (NegotiationStatus.PENDING, NegotiationStatus.IN_PROGRESS),
            (NegotiationStatus.IN_PROGRESS, NegotiationStatus.AWAITING_APPROVAL),
            (NegotiationStatus.AWAITING_APPROVAL, NegotiationStatus.COMPLETED),
        ]
        for from_s, to_s in transitions:
            assert can_transition(from_s, to_s) is True

    def test_cancellation_from_any_non_terminal(self) -> None:
        """User can cancel from PENDING, IN_PROGRESS, or AWAITING_APPROVAL."""
        for status in [
            NegotiationStatus.PENDING,
            NegotiationStatus.IN_PROGRESS,
            NegotiationStatus.AWAITING_APPROVAL,
        ]:
            assert can_transition(status, NegotiationStatus.CANCELLED) is True
