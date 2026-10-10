"""
Base exceptions for Legatio AI domain.
All domain-specific exceptions inherit from LegatioBaseException.
This allows consistent error handling across the codebase.
"""

from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class LegatioBaseException(Exception):
    """Base exception for all Legatio domain errors."""

    default_code: str = "legatio_error"
    default_status: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, code: str | None = None) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        super().__init__(self.message)


# -----------------------------------------------------------------------------
# Policy Engine Exceptions
# -----------------------------------------------------------------------------
class PolicyEngineError(LegatioBaseException):
    """Base exception for Policy Engine errors."""

    default_code: str = "policy_engine_error"
    default_message: str = "Policy evaluation failed."


class PolicyEvaluationError(PolicyEngineError):
    """Raised when policy evaluation encounters an unexpected error."""

    default_code: str = "policy_evaluation_error"
    default_message: str = "Policy evaluation failed unexpectedly."


class InvalidRuleError(PolicyEngineError):
    """Raised when a rule is malformed or invalid."""

    default_code: str = "invalid_rule"
    default_message: str = "The rule is invalid or malformed."


class InvalidActionError(PolicyEngineError):
    """Raised when a proposed action is malformed."""

    default_code: str = "invalid_action"
    default_message: str = "The proposed action is invalid or malformed."


# -----------------------------------------------------------------------------
# Constitution Exceptions
# -----------------------------------------------------------------------------
class ConstitutionError(LegatioBaseException):
    """Base exception for Constitution-related errors."""

    default_code: str = "constitution_error"


class ConstitutionNotFoundError(ConstitutionError):
    """Raised when a constitution does not exist."""

    default_code: str = "constitution_not_found"
    default_status: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Constitution not found."


class NoActiveConstitutionError(ConstitutionError):
    """Raised when an agent has no active constitution."""

    default_code: str = "no_active_constitution"
    default_message: str = "The agent has no active constitution."


class ConstitutionImmutableError(ConstitutionError):
    """Raised when attempting to modify an immutable constitution version."""

    default_code: str = "constitution_immutable"
    default_message: str = "This constitution version is immutable."


class MultipleActiveConstitutionsError(ConstitutionError):
    """Raised when attempting to activate a second constitution for an agent."""

    default_code: str = "multiple_active_constitutions"
    default_message: str = "An agent can only have one active constitution at a time."


# -----------------------------------------------------------------------------
# Negotiation Exceptions
# -----------------------------------------------------------------------------
class NegotiationError(LegatioBaseException):
    """Base exception for Negotiation-related errors."""

    default_code: str = "negotiation_error"


class NegotiationNotFoundError(NegotiationError):
    """Raised when a negotiation room does not exist."""

    default_code: str = "negotiation_not_found"
    default_status: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Negotiation room not found."


class NegotiationStateError(NegotiationError):
    """Raised when a state transition is invalid."""

    default_code: str = "negotiation_state_error"
    default_message: str = "Invalid state transition for negotiation."


class MaxRoundsExceededError(NegotiationError):
    """Raised when max rounds is exceeded."""

    default_code: str = "max_rounds_exceeded"
    default_message: str = "Maximum negotiation rounds exceeded."


# -----------------------------------------------------------------------------
# Proposal Exceptions
# -----------------------------------------------------------------------------
class ProposalError(LegatioBaseException):
    """Base exception for Proposal-related errors."""

    default_code: str = "proposal_error"


class ProposalNotFoundError(ProposalError):
    """Raised when a proposal does not exist."""

    default_code: str = "proposal_not_found"
    default_status: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Proposal not found."


class ProposalAlreadyEvaluatedError(ProposalError):
    """Raised when attempting to evaluate an already-evaluated proposal."""

    default_code: str = "proposal_already_evaluated"
    default_message: str = "This proposal has already been evaluated."


# -----------------------------------------------------------------------------
# Approval Exceptions
# -----------------------------------------------------------------------------
class ApprovalError(LegatioBaseException):
    """Base exception for Approval-related errors."""

    default_code: str = "approval_error"


class ApprovalNotFoundError(ApprovalError):
    """Raised when an approval request does not exist."""

    default_code: str = "approval_not_found"
    default_status: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Approval request not found."


class ApprovalAlreadyDecidedError(ApprovalError):
    """Raised when attempting to decide an already-decided approval."""

    default_code: str = "approval_already_decided"
    default_message: str = "This approval request has already been decided."


class ApprovalExpiredError(ApprovalError):
    """Raised when attempting to decide an expired approval."""

    default_code: str = "approval_expired"
    default_status: int = status.HTTP_410_GONE
    default_message: str = "This approval request has expired."


class ApprovalUnauthorizedError(ApprovalError):
    """Raised when a user tries to decide an approval they don't own."""

    default_code: str = "approval_unauthorized"
    default_status: int = status.HTTP_403_FORBIDDEN
    default_message: str = "You are not authorized to decide this approval."


class ApprovalStateError(ApprovalError):
    """Raised when an invalid approval state transition is attempted.

    Source: 04-BUSINESS-FLOW.md Section 8.3
    """

    default_code: str = "approval_state_error"
    default_message: str = "Invalid state transition for approval request."


# -----------------------------------------------------------------------------
# Agreement Exceptions
# -----------------------------------------------------------------------------
class AgreementError(LegatioBaseException):
    """Base exception for Agreement-related errors."""

    default_code: str = "agreement_error"


class AgreementNotFoundError(AgreementError):
    """Raised when an agreement does not exist."""

    default_code: str = "agreement_not_found"
    default_status: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Agreement not found."


class AgreementNotInDraftError(AgreementError):
    """Raised when attempting to sign a non-draft agreement."""

    default_code: str = "agreement_not_in_draft"
    default_message: str = "Agreement is not in DRAFT status."


class HashMismatchError(AgreementError):
    """Raised when canonical hash does not match."""

    default_code: str = "hash_mismatch"
    default_status: int = status.HTTP_409_CONFLICT
    default_message: str = "Agreement has been tampered with. Hash mismatch."


# -----------------------------------------------------------------------------
# Audit Exceptions
# -----------------------------------------------------------------------------
class AuditError(LegatioBaseException):
    """Base exception for Audit-related errors."""

    default_code: str = "audit_error"


class AuditChainBrokenError(AuditError):
    """Raised when the audit hash chain is broken."""

    default_code: str = "audit_chain_broken"
    default_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "Audit hash chain integrity check failed."


class AuditImmutableError(AuditError):
    """Raised when attempting to modify an audit event."""

    default_code: str = "audit_immutable"
    default_message: str = "AuditEvent records are immutable."


# -----------------------------------------------------------------------------
# Authentication Exceptions
# -----------------------------------------------------------------------------
class AuthenticationError(LegatioBaseException):
    """Base exception for authentication errors."""

    default_code: str = "authentication_error"
    default_status: int = status.HTTP_401_UNAUTHORIZED
    default_message: str = "Authentication failed."


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    default_code: str = "invalid_credentials"
    default_message: str = "Invalid email or password."


class TwoFactorRequiredError(AuthenticationError):
    """Raised when 2FA is required but not provided."""

    default_code: str = "two_factor_required"
    default_status: int = status.HTTP_403_FORBIDDEN
    default_message: str = "Two-factor authentication is required."


class InvalidTOTPError(AuthenticationError):
    """Raised when TOTP code is invalid."""

    default_code: str = "invalid_totp"
    default_message: str = "Invalid TOTP code."


# -----------------------------------------------------------------------------
# Custom DRF exception handler
# -----------------------------------------------------------------------------
def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler that standardizes error responses.
    """
    response = exception_handler(exc, context)

    if isinstance(exc, LegatioBaseException):
        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
            status=exc.default_status,
        )

    if response is not None:
        response.data = {
            "error": {
                "code": getattr(exc, "default_code", "error"),
                "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
                "details": response.data,
            }
        }

    return response


class ProposalStateError(Exception):
    """Raised when an invalid proposal state transition is attempted.
    Source: 04-BUSINESS-FLOW.md Section 8.2
    """

    pass
