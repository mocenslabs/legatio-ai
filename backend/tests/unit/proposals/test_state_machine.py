"""
Unit tests for the Proposal state machine.

Source: 04-BUSINESS-FLOW.md Section 8.2
"""

import pytest

from apps.proposals.state_machine import (
    can_transition,
    is_terminal,
    validate_transition,
)
from core.enums import ProposalStatus
from core.exceptions import ProposalStateError


class TestValidTransitions:
    """Tests for valid state transitions."""

    def test_received_to_evaluating(self) -> None:
        assert can_transition(ProposalStatus.RECEIVED, ProposalStatus.EVALUATING) is True

    def test_evaluating_to_allowed(self) -> None:
        assert can_transition(ProposalStatus.EVALUATING, ProposalStatus.ALLOWED) is True

    def test_evaluating_to_denied(self) -> None:
        assert can_transition(ProposalStatus.EVALUATING, ProposalStatus.DENIED) is True

    def test_evaluating_to_pending_approval(self) -> None:
        assert can_transition(ProposalStatus.EVALUATING, ProposalStatus.PENDING_APPROVAL) is True

    def test_allowed_to_accepted(self) -> None:
        assert can_transition(ProposalStatus.ALLOWED, ProposalStatus.ACCEPTED) is True

    def test_allowed_to_rejected(self) -> None:
        assert can_transition(ProposalStatus.ALLOWED, ProposalStatus.REJECTED) is True

    def test_denied_to_superseded(self) -> None:
        assert can_transition(ProposalStatus.DENIED, ProposalStatus.SUPERSEDED) is True

    def test_pending_approval_to_accepted(self) -> None:
        assert can_transition(ProposalStatus.PENDING_APPROVAL, ProposalStatus.ACCEPTED) is True

    def test_pending_approval_to_rejected(self) -> None:
        assert can_transition(ProposalStatus.PENDING_APPROVAL, ProposalStatus.REJECTED) is True

    def test_pending_approval_to_expired(self) -> None:
        assert can_transition(ProposalStatus.PENDING_APPROVAL, ProposalStatus.EXPIRED) is True

    def test_accepted_to_superseded(self) -> None:
        assert can_transition(ProposalStatus.ACCEPTED, ProposalStatus.SUPERSEDED) is True


class TestInvalidTransitions:
    """Tests for invalid state transitions."""

    def test_received_to_allowed_invalid(self) -> None:
        assert can_transition(ProposalStatus.RECEIVED, ProposalStatus.ALLOWED) is False

    def test_received_to_denied_invalid(self) -> None:
        assert can_transition(ProposalStatus.RECEIVED, ProposalStatus.DENIED) is False

    def test_evaluating_to_accepted_invalid(self) -> None:
        assert can_transition(ProposalStatus.EVALUATING, ProposalStatus.ACCEPTED) is False

    def test_terminal_states_no_transitions(self) -> None:
        """Terminal states cannot transition to any other state."""
        for terminal in [
            ProposalStatus.REJECTED,
            ProposalStatus.SUPERSEDED,
            ProposalStatus.EXPIRED,
        ]:
            for target in ProposalStatus:
                if target != terminal:
                    assert can_transition(terminal, target) is False


class TestValidateTransition:
    def test_valid_transition_passes(self) -> None:
        validate_transition(ProposalStatus.RECEIVED, ProposalStatus.EVALUATING)

    def test_invalid_transition_raises(self) -> None:
        with pytest.raises(ProposalStateError, match="Invalid transition"):
            validate_transition(ProposalStatus.REJECTED, ProposalStatus.RECEIVED)


class TestTerminalStates:
    def test_rejected_is_terminal(self) -> None:
        assert is_terminal(ProposalStatus.REJECTED) is True

    def test_superseded_is_terminal(self) -> None:
        assert is_terminal(ProposalStatus.SUPERSEDED) is True

    def test_expired_is_terminal(self) -> None:
        assert is_terminal(ProposalStatus.EXPIRED) is True

    def test_received_is_not_terminal(self) -> None:
        assert is_terminal(ProposalStatus.RECEIVED) is False

    def test_evaluating_is_not_terminal(self) -> None:
        assert is_terminal(ProposalStatus.EVALUATING) is False

    def test_allowed_is_not_terminal(self) -> None:
        assert is_terminal(ProposalStatus.ALLOWED) is False


class TestFullLifecycle:
    """Test the full happy-path lifecycle."""

    def test_happy_path_allowed(self) -> None:
        """RECEIVED → EVALUATING → ALLOWED → ACCEPTED."""
        transitions = [
            (ProposalStatus.RECEIVED, ProposalStatus.EVALUATING),
            (ProposalStatus.EVALUATING, ProposalStatus.ALLOWED),
            (ProposalStatus.ALLOWED, ProposalStatus.ACCEPTED),
        ]
        for from_s, to_s in transitions:
            assert can_transition(from_s, to_s) is True

    def test_happy_path_denied(self) -> None:
        """RECEIVED → EVALUATING → DENIED → SUPERSEDED."""
        transitions = [
            (ProposalStatus.RECEIVED, ProposalStatus.EVALUATING),
            (ProposalStatus.EVALUATING, ProposalStatus.DENIED),
            (ProposalStatus.DENIED, ProposalStatus.SUPERSEDED),
        ]
        for from_s, to_s in transitions:
            assert can_transition(from_s, to_s) is True

    def test_happy_path_approval(self) -> None:
        """RECEIVED → EVALUATING → PENDING_APPROVAL → ACCEPTED."""
        transitions = [
            (ProposalStatus.RECEIVED, ProposalStatus.EVALUATING),
            (ProposalStatus.EVALUATING, ProposalStatus.PENDING_APPROVAL),
            (ProposalStatus.PENDING_APPROVAL, ProposalStatus.ACCEPTED),
        ]
        for from_s, to_s in transitions:
            assert can_transition(from_s, to_s) is True
