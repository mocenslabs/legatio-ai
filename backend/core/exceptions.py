"""
Custom exceptions for Legatio AI.
"""


class LegatioBaseError(Exception):
    """Base exception for all Legatio exceptions."""

    pass


class PolicyEvaluationError(LegatioBaseError):
    """Raised when policy evaluation fails."""

    pass


class ConstitutionNotFoundError(LegatioBaseError):
    """Raised when a constitution is not found."""

    pass


class NegotiationError(LegatioBaseError):
    """Raised when a negotiation operation fails."""

    pass


class ApprovalError(LegatioBaseError):
    """Raised when an approval operation fails."""

    pass
