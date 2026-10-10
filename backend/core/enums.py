"""
System-wide enums for Legatio AI.

All enums are defined as Django TextChoices for database compatibility
and Python Enum for type safety.

Source of truth: 03-DATA-MODEL.md Section 5
"""

from django.db import models


# =============================================================================
# 5.1 AgentType
# =============================================================================
class AgentType(models.TextChoices):
    """Type of agent in the system."""

    USER_AGENT = "USER_AGENT", "User Agent"
    EXTERNAL_AGENT = "EXTERNAL_AGENT", "External Agent"
    SIMULATED = "SIMULATED", "Simulated"


# =============================================================================
# 5.2 AgentStatus
# =============================================================================
class AgentStatus(models.TextChoices):
    """Lifecycle status of an agent."""

    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    REVOKED = "REVOKED", "Revoked"


# =============================================================================
# 5.3 ConstitutionStatus
# =============================================================================
class ConstitutionStatus(models.TextChoices):
    """Lifecycle status of a constitution or constitution version."""

    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Active"
    ARCHIVED = "ARCHIVED", "Archived"


# =============================================================================
# 5.4 RuleCategory
# =============================================================================
class RuleCategory(models.TextChoices):
    """Category of a policy rule."""

    FINANCIAL = "FINANCIAL", "Financial"
    PRIVACY = "PRIVACY", "Privacy"
    NEGOTIATION = "NEGOTIATION", "Negotiation"
    CUSTOM = "CUSTOM", "Custom"


# =============================================================================
# 5.5 RuleAction
# =============================================================================
class RuleAction(models.TextChoices):
    """Action to take when a rule matches."""

    ALLOW = "ALLOW", "Allow"
    DENY = "DENY", "Deny"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL", "Require Approval"


# =============================================================================
# 5.6 RuleOperator
# =============================================================================
class RuleOperator(models.TextChoices):
    """Comparison operator for rule conditions."""

    EQUALS = "EQUALS", "Equals"
    NOT_EQUALS = "NOT_EQUALS", "Not Equals"
    GREATER_THAN = "GREATER_THAN", "Greater Than"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL", "Greater Than or Equal"
    LESS_THAN = "LESS_THAN", "Less Than"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL", "Less Than or Equal"
    CONTAINS = "CONTAINS", "Contains"
    NOT_CONTAINS = "NOT_CONTAINS", "Not Contains"
    IN = "IN", "In"
    NOT_IN = "NOT_IN", "Not In"


# =============================================================================
# 5.7 NegotiationStatus
# =============================================================================
class NegotiationStatus(models.TextChoices):
    """Lifecycle status of a negotiation room."""

    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    AWAITING_APPROVAL = "AWAITING_APPROVAL", "Awaiting Approval"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    FAILED = "FAILED", "Failed"
    EXPIRED = "EXPIRED", "Expired"


# =============================================================================
# 5.8 ProposalStatus
# =============================================================================
class ProposalStatus(models.TextChoices):
    """Lifecycle status of a proposal."""

    RECEIVED = "RECEIVED", "Received"
    EVALUATING = "EVALUATING", "Evaluating"
    ALLOWED = "ALLOWED", "Allowed"
    DENIED = "DENIED", "Denied"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED", "Superseded"


# =============================================================================
# 5.9 PolicyDecisionOutcome
# =============================================================================
class PolicyDecisionOutcome(models.TextChoices):
    """Outcome of a policy evaluation."""

    ALLOW = "ALLOW", "Allow"
    DENY = "DENY", "Deny"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL", "Require Human Approval"
    ERROR = "ERROR", "Error"


# =============================================================================
# 5.10 RiskLevel
# =============================================================================
class RiskLevel(models.TextChoices):
    """Risk level assigned to a policy decision or action."""

    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


# =============================================================================
# 5.11 ApprovalStatus
# =============================================================================
class ApprovalStatus(models.TextChoices):
    """Lifecycle status of an approval request."""

    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    MODIFIED = "MODIFIED", "Modified"
    EXPIRED = "EXPIRED", "Expired"


# =============================================================================
# 5.12 AgreementStatus
# =============================================================================
class AgreementStatus(models.TextChoices):
    """Lifecycle status of an agreement."""

    DRAFT = "DRAFT", "Draft"
    SIGNED = "SIGNED", "Signed"
    EXECUTED = "EXECUTED", "Executed"
    VOIDED = "VOIDED", "Voided"


# =============================================================================
# 5.13 NotificationChannel
# =============================================================================
class NotificationChannel(models.TextChoices):
    """Channel through which a notification is delivered."""

    WEBSOCKET = "WEBSOCKET", "WebSocket"
    EMAIL = "EMAIL", "Email"
    PUSH = "PUSH", "Push"


# =============================================================================
# 5.14 NotificationStatus
# =============================================================================
class NotificationStatus(models.TextChoices):
    """Delivery status of a notification."""

    PENDING = "PENDING", "Pending"
    DELIVERED = "DELIVERED", "Delivered"
    READ = "READ", "Read"
    FAILED = "FAILED", "Failed"


# =============================================================================
# 5.15 ActorType (Audit)
# =============================================================================
class ActorType(models.TextChoices):
    """Type of actor that triggered an audit event."""

    USER = "USER", "User"
    AGENT = "AGENT", "Agent"
    SYSTEM = "SYSTEM", "System"
    ADMIN = "ADMIN", "Admin"
    EXTERNAL_AGENT = "EXTERNAL_AGENT", "External Agent"


# =============================================================================
# 5.16 EventType (Audit)
# =============================================================================
class EventType(models.TextChoices):
    """Type of audit event."""

    # Account events
    USER_REGISTERED = "user.registered", "User Registered"
    USER_LOGIN = "user.login", "User Login"
    USER_2FA_ENABLED = "user.2fa.enabled", "User 2FA Enabled"

    # Agent events
    AGENT_CREATED = "agent.created", "Agent Created"
    AGENT_SUSPENDED = "agent.suspended", "Agent Suspended"
    AGENT_CREDENTIAL_ROTATED = "agent.credential.rotated", "Agent Credential Rotated"

    # Constitution events
    CONSTITUTION_CREATED = "constitution.created", "Constitution Created"
    CONSTITUTION_VERSION_ACTIVATED = (
        "constitution.version.activated",
        "Constitution Version Activated",
    )
    CONSTITUTION_RULE_ADDED = "constitution.rule.added", "Constitution Rule Added"

    # Negotiation events
    NEGOTIATION_STARTED = "negotiation.started", "Negotiation Started"
    NEGOTIATION_MESSAGE_CREATED = "negotiation.message.created", "Negotiation Message Created"
    NEGOTIATION_COMPLETED = "negotiation.completed", "Negotiation Completed"
    NEGOTIATION_CANCELLED = "negotiation.cancelled", "Negotiation Cancelled"
    NEGOTIATION_EXPIRED = "negotiation.expired", "Negotiation Expired"
    NEGOTIATION_FAILED = "negotiation.failed", "Negotiation Failed"

    # Proposal events
    PROPOSAL_RECEIVED = "proposal.received", "Proposal Received"
    PROPOSAL_EVALUATED = "proposal.evaluated", "Proposal Evaluated"
    PROPOSAL_DENIED = "proposal.denied", "Proposal Denied"
    COUNTERPROPOSAL_CREATED = "counterproposal.created", "Counterproposal Created"

    # Approval events
    APPROVAL_REQUESTED = "approval.requested", "Approval Requested"
    APPROVAL_APPROVED = "approval.approved", "Approval Approved"
    APPROVAL_REJECTED = "approval.rejected", "Approval Rejected"
    APPROVAL_EXPIRED = "approval.expired", "Approval Expired"

    # Agreement events
    AGREEMENT_CREATED = "agreement.created", "Agreement Created"
    AGREEMENT_SIGNED = "agreement.signed", "Agreement Signed"
    AGREEMENT_EXECUTED = "agreement.executed", "Agreement Executed"
    AGREEMENT_VOIDED = "agreement.voided", "Agreement Voided"

    # System events
    SYSTEM_POLICY_ERROR = "system.policy_error", "System Policy Error"
    SYSTEM_INTEGRITY_CHECK_PASSED = "system.integrity_check.passed", "System Integrity Check Passed"
    SYSTEM_INTEGRITY_CHECK_FAILED = "system.integrity_check.failed", "System Integrity Check Failed"


# =============================================================================
# Additional Enums (not in 03-DATA-MODEL.md but required by the system)
# =============================================================================
class NegotiationMessageType(models.TextChoices):
    """Type of message in a negotiation room."""

    TEXT = "TEXT", "Text"
    PROPOSAL = "PROPOSAL", "Proposal"
    COUNTERPROPOSAL = "COUNTERPROPOSAL", "Counterproposal"
    SYSTEM = "SYSTEM", "System"


class SignatureAlgorithm(models.TextChoices):
    """Algorithm used for agreement signatures."""

    HMAC_SHA256 = "HMAC-SHA256", "HMAC-SHA256"


class ProposalActionType(models.TextChoices):
    """Type of action proposed by an agent."""

    PURCHASE = "purchase", "Purchase"
    SUBSCRIBE = "subscribe", "Subscribe"
    SHARE_DATA = "share_data", "Share Data"
    RENT = "rent", "Rent"
    BOOK = "book", "Book"
    OTHER = "other", "Other"
