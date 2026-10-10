"""
Unit tests for core enums.
Verifies that all enums are correctly defined and have the expected values
as specified in 03-DATA-MODEL.md Section 5.
"""

from core.enums import (
    ActorType,
    AgentStatus,
    AgentType,
    AgreementStatus,
    ApprovalStatus,
    ConstitutionStatus,
    EventType,
    NegotiationMessageType,
    NegotiationStatus,
    NotificationChannel,
    NotificationStatus,
    PolicyDecisionOutcome,
    ProposalActionType,
    ProposalStatus,
    RiskLevel,
    RuleAction,
    RuleCategory,
    RuleOperator,
    SignatureAlgorithm,
)


class TestAgentEnums:
    def test_agent_type_values(self) -> None:
        assert AgentType.USER_AGENT == "USER_AGENT"
        assert AgentType.EXTERNAL_AGENT == "EXTERNAL_AGENT"
        assert AgentType.SIMULATED == "SIMULATED"
        assert len(AgentType.choices) == 3

    def test_agent_status_values(self) -> None:
        assert AgentStatus.ACTIVE == "ACTIVE"
        assert AgentStatus.SUSPENDED == "SUSPENDED"
        assert AgentStatus.REVOKED == "REVOKED"
        assert len(AgentStatus.choices) == 3


class TestConstitutionEnums:
    def test_constitution_status_values(self) -> None:
        assert ConstitutionStatus.DRAFT == "DRAFT"
        assert ConstitutionStatus.ACTIVE == "ACTIVE"
        assert ConstitutionStatus.ARCHIVED == "ARCHIVED"
        assert len(ConstitutionStatus.choices) == 3

    def test_rule_category_values(self) -> None:
        assert RuleCategory.FINANCIAL == "FINANCIAL"
        assert RuleCategory.PRIVACY == "PRIVACY"
        assert RuleCategory.NEGOTIATION == "NEGOTIATION"
        assert RuleCategory.CUSTOM == "CUSTOM"
        assert len(RuleCategory.choices) == 4

    def test_rule_action_values(self) -> None:
        assert RuleAction.ALLOW == "ALLOW"
        assert RuleAction.DENY == "DENY"
        assert RuleAction.REQUIRE_APPROVAL == "REQUIRE_APPROVAL"
        assert len(RuleAction.choices) == 3

    def test_rule_operator_values(self) -> None:
        expected = [
            "EQUALS",
            "NOT_EQUALS",
            "GREATER_THAN",
            "GREATER_THAN_OR_EQUAL",
            "LESS_THAN",
            "LESS_THAN_OR_EQUAL",
            "CONTAINS",
            "NOT_CONTAINS",
            "IN",
            "NOT_IN",
        ]
        for op in expected:
            assert hasattr(RuleOperator, op)
        assert len(RuleOperator.choices) == 10


class TestNegotiationEnums:
    def test_negotiation_status_values(self) -> None:
        expected = [
            "PENDING",
            "IN_PROGRESS",
            "AWAITING_APPROVAL",
            "COMPLETED",
            "CANCELLED",
            "FAILED",
            "EXPIRED",
        ]
        for status in expected:
            assert hasattr(NegotiationStatus, status)
        assert len(NegotiationStatus.choices) == 7

    def test_proposal_status_values(self) -> None:
        expected = [
            "RECEIVED",
            "EVALUATING",
            "ALLOWED",
            "DENIED",
            "PENDING_APPROVAL",
            "ACCEPTED",
            "REJECTED",
            "SUPERSEDED",
        ]
        for status in expected:
            assert hasattr(ProposalStatus, status)
        assert len(ProposalStatus.choices) == 9


class TestPolicyEngineEnums:
    def test_policy_decision_outcome_values(self) -> None:
        assert PolicyDecisionOutcome.ALLOW == "ALLOW"
        assert PolicyDecisionOutcome.DENY == "DENY"
        assert PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL == "REQUIRE_HUMAN_APPROVAL"
        assert PolicyDecisionOutcome.ERROR == "ERROR"
        assert len(PolicyDecisionOutcome.choices) == 4

    def test_risk_level_values(self) -> None:
        assert RiskLevel.LOW == "LOW"
        assert RiskLevel.MEDIUM == "MEDIUM"
        assert RiskLevel.HIGH == "HIGH"
        assert RiskLevel.CRITICAL == "CRITICAL"
        assert len(RiskLevel.choices) == 4


class TestApprovalAndAgreementEnums:
    def test_approval_status_values(self) -> None:
        expected = ["PENDING", "APPROVED", "REJECTED", "MODIFIED", "EXPIRED"]
        for status in expected:
            assert hasattr(ApprovalStatus, status)
        assert len(ApprovalStatus.choices) == 5

    def test_agreement_status_values(self) -> None:
        assert AgreementStatus.DRAFT == "DRAFT"
        assert AgreementStatus.SIGNED == "SIGNED"
        assert AgreementStatus.EXECUTED == "EXECUTED"
        assert AgreementStatus.VOIDED == "VOIDED"
        assert len(AgreementStatus.choices) == 4


class TestNotificationEnums:
    def test_notification_channel_values(self) -> None:
        assert NotificationChannel.WEBSOCKET == "WEBSOCKET"
        assert NotificationChannel.EMAIL == "EMAIL"
        assert NotificationChannel.PUSH == "PUSH"
        assert len(NotificationChannel.choices) == 3

    def test_notification_status_values(self) -> None:
        expected = ["PENDING", "DELIVERED", "READ", "FAILED"]
        for status in expected:
            assert hasattr(NotificationStatus, status)
        assert len(NotificationStatus.choices) == 4


class TestAuditEnums:
    def test_actor_type_values(self) -> None:
        expected = ["USER", "AGENT", "SYSTEM", "ADMIN", "EXTERNAL_AGENT"]
        for actor in expected:
            assert hasattr(ActorType, actor)
        assert len(ActorType.choices) == 5

    def test_event_type_has_all_required_events(self) -> None:
        required_events = [
            "USER_REGISTERED",
            "USER_LOGIN",
            "USER_2FA_ENABLED",
            "AGENT_CREATED",
            "AGENT_SUSPENDED",
            "AGENT_CREDENTIAL_ROTATED",
            "CONSTITUTION_CREATED",
            "CONSTITUTION_VERSION_ACTIVATED",
            "CONSTITUTION_RULE_ADDED",
            "NEGOTIATION_STARTED",
            "NEGOTIATION_MESSAGE_CREATED",
            "NEGOTIATION_COMPLETED",
            "NEGOTIATION_CANCELLED",
            "PROPOSAL_RECEIVED",
            "PROPOSAL_EVALUATED",
            "PROPOSAL_DENIED",
            "COUNTERPROPOSAL_CREATED",
            "APPROVAL_REQUESTED",
            "APPROVAL_APPROVED",
            "APPROVAL_REJECTED",
            "APPROVAL_EXPIRED",
            "AGREEMENT_CREATED",
            "AGREEMENT_SIGNED",
            "AGREEMENT_EXECUTED",
            "AGREEMENT_VOIDED",
            "SYSTEM_POLICY_ERROR",
            "SYSTEM_INTEGRITY_CHECK_FAILED",
        ]
        for event in required_events:
            assert hasattr(EventType, event), f"Missing event: {event}"


class TestAdditionalEnums:
    def test_negotiation_message_type_values(self) -> None:
        expected = ["TEXT", "PROPOSAL", "COUNTERPROPOSAL", "SYSTEM"]
        for msg_type in expected:
            assert hasattr(NegotiationMessageType, msg_type)
        assert len(NegotiationMessageType.choices) == 4

    def test_signature_algorithm_values(self) -> None:
        # FIX: Use .value for enum comparison
        assert SignatureAlgorithm.HMAC_SHA256.value == "HMAC-SHA256"

    def test_proposal_action_type_values(self) -> None:
        expected = ["PURCHASE", "SUBSCRIBE", "SHARE_DATA", "RENT", "BOOK", "OTHER"]
        for action in expected:
            assert hasattr(ProposalActionType, action)
