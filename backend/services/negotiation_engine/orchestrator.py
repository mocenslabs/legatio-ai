"""
Negotiation Orchestrator.

Coordinates the complete lifecycle of a negotiation:
- Creates NegotiationRoom
- Manages state transitions
- Calls simulated agents
- Evaluates proposals with Policy Engine
- Creates Proposal, PolicyDecision, CounterProposal records
- Generates AuditEvents

Source: 04-BUSINESS-FLOW.md Section 4
Source: 05-ROADMAP.md Section 7.3 (Deliverables 3.9, 3.10, 3.11)
"""

import logging
from types import SimpleNamespace
from typing import Any, cast

from django.utils import timezone

from apps.agents.models import Agent
from apps.approvals.services import create_approval_request
from apps.audit.services import create_audit_event
from apps.constitutions.models import Constitution
from apps.negotiations.models import NegotiationMessage, NegotiationRoom
from apps.proposals.models import (
    CounterProposal,
    Proposal,
)
from apps.proposals.models import (
    PolicyDecision as PolicyDecisionModel,
)
from core.enums import (
    ActorType,
    EventType,
    NegotiationMessageType,
    NegotiationStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
)
from core.exceptions import NegotiationStateError
from core.schemas.policy import ProposedAction
from services.negotiation_engine.base import AgentResponse, NegotiationCompletedError
from services.negotiation_engine.counter_offers import generate_counter_offer
from services.negotiation_engine.registry import create_agent
from services.policy_engine.evaluator import evaluate_policy
from services.policy_engine.loader import load_active_rules_for_agent

logger = logging.getLogger("legatio.negotiation.orchestrator")


class NegotiationOrchestrator:
    """
    Orchestrates the complete negotiation lifecycle.

    This class coordinates:
    - NegotiationRoom state transitions
    - Agent interactions (simulated or LLM-based)
    - Policy Engine evaluations
    - Proposal and PolicyDecision creation
    - Audit event generation
    """

    def __init__(self, room: NegotiationRoom) -> None:
        """
        Initialize the orchestrator.

        Args:
            room: The NegotiationRoom to orchestrate.
        """
        self.room = room
        agent_type_key = self._detect_agent_type()
        self._external_agent = create_agent(agent_type_key)

    def _detect_agent_type(self) -> str:
        """Detect which simulated agent to use based on external agent name."""
        name = self.room.external_agent.name.lower()
        if "hotel" in name:
            return "hotel"
        elif "isp" in name or "internet" in name:
            return "isp"
        elif "vendor" in name or "shop" in name:
            return "vendor"
        return "hotel"

    @classmethod
    def create_room(
        cls,
        *,
        user_agent: Agent,
        external_agent: Agent,
        constitution: Constitution,
        title: str,
        user_instruction: str,
        max_rounds: int = 10,
        ttl_hours: int = 24,
        user: Any,
    ) -> NegotiationRoom:
        """
        Create a new NegotiationRoom.

        Args:
            user_agent: The user's agent.
            external_agent: The external agent to negotiate with.
            constitution: The constitution governing the negotiation.
            title: Human-readable title (stored in audit event only).
            user_instruction: Original user instruction (stored in audit event only).
            max_rounds: Maximum number of rounds.
            ttl_hours: Time-to-live in hours.
            user: The user creating the negotiation.

        Returns:
            The created NegotiationRoom.
        """
        year = timezone.now().year
        sequence = NegotiationRoom.all_objects.count() + 1
        reference_code = f"NEG-{year}-{sequence:06d}"

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=external_agent,
            constitution=constitution,
            reference_code=reference_code,
            max_rounds=max_rounds,
            ttl_hours=ttl_hours,
        )

        create_audit_event(
            event_type=EventType.NEGOTIATION_STARTED,
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="NegotiationRoom",
            entity_id=room.id,
            payload={
                "title": title,
                "user_instruction": user_instruction,
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(external_agent.id),
            },
        )

        logger.info(f"NegotiationRoom created: {room.reference_code}")
        return cast(NegotiationRoom, room)

    def start_negotiation(self) -> None:
        """
        Start the negotiation: transition from PENDING to IN_PROGRESS.

        Raises:
            NegotiationStateError: If the transition is invalid.
        """
        self.room.transition_to(NegotiationStatus.IN_PROGRESS)
        logger.info(f"Negotiation started: {self.room.reference_code}")

    def process_round(self) -> dict[str, Any]:
        """
        Process a single round of negotiation.

        Returns:
            Dictionary with round results.
        """
        round_number = self.room.current_round + 1

        if round_number > self.room.max_rounds:
            # Only transition to FAILED if the transition is valid
            # (may not be valid if room is in AWAITING_APPROVAL)
            from apps.negotiations.state_machine import can_transition

            current_status = NegotiationStatus(self.room.status)
            if can_transition(current_status, NegotiationStatus.FAILED):
                self.room.transition_to(NegotiationStatus.FAILED)
                create_audit_event(
                    event_type=EventType.NEGOTIATION_FAILED,
                    actor_type=ActorType.SYSTEM,
                    entity_type="NegotiationRoom",
                    entity_id=self.room.id,
                    payload={"reason": "max_rounds_exceeded"},
                )
            raise NegotiationStateError("Max rounds exceeded")

        agent_response = self._get_agent_response(round_number)
        proposal = self._create_proposal(agent_response, round_number)
        policy_decision = self._evaluate_proposal(proposal)
        result = self._handle_policy_decision(proposal, policy_decision, round_number)
        self.room.increment_round()
        return result

    def _get_agent_response(self, round_number: int) -> AgentResponse:
        """Get response from the external agent."""
        try:
            response = self._external_agent.respond(
                round_number=round_number,
                user_instruction="",
                previous_proposals=[],
                context={"room_id": str(self.room.id)},
            )
            return response
        except NegotiationCompletedError:
            self.room.transition_to(NegotiationStatus.COMPLETED)
            create_audit_event(
                event_type=EventType.NEGOTIATION_COMPLETED,
                actor_type=ActorType.SYSTEM,
                entity_type="NegotiationRoom",
                entity_id=self.room.id,
                payload={"reason": "agent_completed"},
            )
            raise

    def _create_proposal(self, agent_response: AgentResponse, round_number: int) -> Proposal:
        """Create a Proposal record from the agent response."""
        proposal = Proposal.objects.create(
            room=self.room,
            sender=self.room.external_agent,
            action_type=agent_response.action.action_type,
            amount=agent_response.action.amount,
            currency=agent_response.action.currency or "EUR",
            data_fields_requested=agent_response.action.data_fields_requested,
            contract_length_months=agent_response.action.contract_length_months,
            auto_renewal=agent_response.action.auto_renewal,
            terms=agent_response.action.terms or {},
            status=ProposalStatus.RECEIVED,
            round_number=round_number,
        )

        NegotiationMessage.objects.create(
            room=self.room,
            sender_type=ActorType.EXTERNAL_AGENT,
            sender_id=self.room.external_agent.id,
            message_type=NegotiationMessageType.PROPOSAL,
            content={"text": agent_response.natural_language_summary},
            round_number=round_number,
        )

        create_audit_event(
            event_type=EventType.PROPOSAL_RECEIVED,
            actor_type=ActorType.EXTERNAL_AGENT,
            actor_id=self.room.external_agent.id,
            entity_type="Proposal",
            entity_id=proposal.id,
            payload={
                "action_type": proposal.action_type,
                "amount": str(proposal.amount) if proposal.amount else None,
                "round_number": round_number,
            },
        )

        return proposal

    def _evaluate_proposal(self, proposal: Proposal) -> PolicyDecisionModel:
        """Evaluate the proposal with the Policy Engine."""
        # Transition proposal to EVALUATING (state machine requires this step)
        proposal.transition_to(ProposalStatus.EVALUATING)
        rules = load_active_rules_for_agent(self.room.user_agent)

        action = ProposedAction(
            action_type=proposal.action_type,
            amount=proposal.amount,
            currency=proposal.currency,
            data_fields_requested=proposal.data_fields_requested,
            contract_length_months=proposal.contract_length_months,
            auto_renewal=proposal.auto_renewal,
            category=proposal.terms.get("category"),
            is_new_vendor=proposal.terms.get("is_new_vendor", False),
            terms=proposal.terms,
        )

        decision = evaluate_policy(action, rules)

        policy_decision = PolicyDecisionModel.objects.create(
            proposal=proposal,
            constitution_version=self.room.constitution.active_version,
            outcome=decision.outcome,
            risk_level=decision.risk_level,
            reason=decision.reason,
            matched_rules=[
                {
                    "rule_id": str(mr.rule_id) if hasattr(mr, "rule_id") else None,
                    "rule_number": mr.rule_number if hasattr(mr, "rule_number") else None,
                    "name": mr.name if hasattr(mr, "name") else None,
                    "action": mr.action.value
                    if hasattr(mr, "action") and hasattr(mr.action, "value")
                    else str(mr.action)
                    if hasattr(mr, "action")
                    else None,
                    "triggered_by": mr.triggered_by if hasattr(mr, "triggered_by") else None,
                }
                for mr in (decision.matched_rules or [])
            ],
            evaluation_duration_ms=decision.evaluation_duration_ms,
            engine_version=decision.engine_version,
        )

        create_audit_event(
            event_type=EventType.PROPOSAL_EVALUATED,
            actor_type=ActorType.SYSTEM,
            entity_type="PolicyDecision",
            entity_id=policy_decision.id,
            payload={
                "proposal_id": str(proposal.id),
                "outcome": decision.outcome,
                "risk_level": decision.risk_level,
                "reason": decision.reason,
            },
        )

        return cast(PolicyDecisionModel, policy_decision)

    def _handle_policy_decision(
        self,
        proposal: Proposal,
        policy_decision: PolicyDecisionModel,
        round_number: int,
    ) -> dict[str, Any]:
        """Handle the policy decision outcome."""
        outcome = policy_decision.outcome

        if outcome == PolicyDecisionOutcome.DENY:
            return self._handle_denial(proposal, policy_decision, round_number)
        elif outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL:
            return self._handle_approval_required(proposal, policy_decision)
        elif outcome == PolicyDecisionOutcome.ALLOW:
            return self._handle_allow(proposal, policy_decision)
        else:
            return self._handle_error(proposal, policy_decision)

    def _handle_denial(
        self,
        proposal: Proposal,
        policy_decision: PolicyDecisionModel,
        round_number: int,
    ) -> dict[str, Any]:
        """Handle DENY outcome: generate counter-offer."""
        proposal.transition_to(ProposalStatus.DENIED)

        create_audit_event(
            event_type=EventType.PROPOSAL_DENIED,
            actor_type=ActorType.SYSTEM,
            entity_type="Proposal",
            entity_id=proposal.id,
            payload={"reason": policy_decision.reason},
        )

        original_action = ProposedAction(
            action_type=proposal.action_type,
            amount=proposal.amount,
            currency=proposal.currency,
            data_fields_requested=proposal.data_fields_requested,
            contract_length_months=proposal.contract_length_months,
            auto_renewal=proposal.auto_renewal,
            terms=proposal.terms,
        )

        # generate_counter_offer expects a schema PolicyDecision (only uses .reason)
        schema_decision = SimpleNamespace(reason=policy_decision.reason)
        counter_action = generate_counter_offer(original_action, schema_decision)

        counter_proposal = CounterProposal.objects.create(
            proposal=proposal,
            sender=self.room.user_agent,
            adjustments={
                "amount": str(counter_action.amount) if counter_action.amount else None,
                "data_fields_requested": counter_action.data_fields_requested,
                "contract_length_months": counter_action.contract_length_months,
                "auto_renewal": counter_action.auto_renewal,
            },
            reasoning=f"Counter-offer generated in response to denial: {policy_decision.reason}",
        )

        create_audit_event(
            event_type=EventType.COUNTERPROPOSAL_CREATED,
            actor_type=ActorType.AGENT,
            actor_id=self.room.user_agent.id,
            entity_type="CounterProposal",
            entity_id=counter_proposal.id,
            payload={
                "proposal_id": str(proposal.id),
                "adjustments": counter_proposal.adjustments,
            },
        )

        return {
            "round_number": round_number,
            "proposal": proposal,
            "policy_decision": policy_decision,
            "outcome": "DENY",
            "counter_offer": counter_proposal,
        }

    def _handle_approval_required(
        self,
        proposal: Proposal,
        policy_decision: PolicyDecisionModel,
    ) -> dict[str, Any]:
        """Handle REQUIRE_HUMAN_APPROVAL outcome."""
        # Only transition room if not already in AWAITING_APPROVAL (idempotent)
        if self.room.status != NegotiationStatus.AWAITING_APPROVAL.value:
            self.room.transition_to(NegotiationStatus.AWAITING_APPROVAL)

        # Create ApprovalRequest (also transitions proposal to PENDING_APPROVAL)
        create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=self.room,
        )

        return {
            "round_number": proposal.round_number,
            "proposal": proposal,
            "policy_decision": policy_decision,
            "outcome": "REQUIRE_HUMAN_APPROVAL",
            "counter_offer": None,
        }

    def _handle_allow(
        self,
        proposal: Proposal,
        policy_decision: PolicyDecisionModel,
    ) -> dict[str, Any]:
        """Handle ALLOW outcome."""
        proposal.transition_to(ProposalStatus.ALLOWED)

        return {
            "round_number": proposal.round_number,
            "proposal": proposal,
            "policy_decision": policy_decision,
            "outcome": "ALLOW",
            "counter_offer": None,
        }

    def _handle_error(
        self,
        proposal: Proposal,
        policy_decision: PolicyDecisionModel,
    ) -> dict[str, Any]:
        """Handle ERROR outcome (treat as DENY)."""
        proposal.transition_to(ProposalStatus.DENIED)

        create_audit_event(
            event_type=EventType.SYSTEM_POLICY_ERROR,
            actor_type=ActorType.SYSTEM,
            entity_type="Proposal",
            entity_id=proposal.id,
            payload={"error": policy_decision.reason},
        )

        return {
            "round_number": proposal.round_number,
            "proposal": proposal,
            "policy_decision": policy_decision,
            "outcome": "ERROR",
            "counter_offer": None,
        }
