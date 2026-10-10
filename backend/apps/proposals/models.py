"""
Models for the proposals app.

Defines Proposal (structured offer), CounterProposal (append-only counter-offer),
and PolicyDecision (append-only evaluation record).

Source: 03-DATA-MODEL.md Section 10
"""

import uuid
from typing import Any

from django.db import models

from apps.proposals.managers import AppendOnlyManager
from apps.proposals.state_machine import (
    is_terminal,
    validate_transition,
)
from core.enums import (
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)


class Proposal(models.Model):
    """
    A structured offer from an agent within a negotiation room.

    Follows a state machine with defined transitions.
    Every Proposal that leaves RECEIVED status MUST have at least one
    PolicyDecision record (enforced at service layer).

    Source: 03-DATA-MODEL.md Section 10.1
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    room = models.ForeignKey(
        "negotiations.NegotiationRoom",
        on_delete=models.CASCADE,
        related_name="proposals",
        help_text="Negotiation room this proposal belongs to.",
    )
    sender = models.ForeignKey(
        "agents.Agent",
        on_delete=models.PROTECT,
        related_name="sent_proposals",
        help_text="Agent that created this proposal.",
    )
    action_type = models.CharField(
        max_length=50,
        help_text="Type of action, e.g., 'purchase', 'share_data', 'subscribe'.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monetary amount involved in the action.",
    )
    currency = models.CharField(
        max_length=3,
        default="",
        blank=True,
        help_text="ISO 4217 currency code.",
    )
    data_fields_requested = models.JSONField(
        default=list,
        blank=True,
        help_text="List of data fields requested, e.g., ['phone_number'].",
    )
    contract_length_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Contract length in months, if applicable.",
    )
    auto_renewal = models.BooleanField(
        default=False,
        help_text="Whether the action involves auto-renewal.",
    )
    terms = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full structured terms of the proposal.",
    )
    status = models.CharField(
        max_length=20,
        choices=ProposalStatus.choices,
        default=ProposalStatus.RECEIVED,
        db_index=True,
    )
    round_number = models.PositiveIntegerField(
        help_text="Round number when this proposal was made.",
    )
    superseded_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supersedes",
        help_text="Newer proposal that supersedes this one.",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legatio_proposals_proposal"
        verbose_name = "proposal"
        verbose_name_plural = "proposals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["room"], name="idx_proposal_room"),
            models.Index(fields=["status"], name="idx_proposal_status"),
        ]

    def __str__(self) -> str:
        amount_str = f"€{self.amount}" if self.amount else "no amount"
        return f"Proposal {self.id} ({amount_str}, {self.get_status_display()})"

    def transition_to(self, new_status: ProposalStatus) -> None:
        """
        Transition to a new status with validation.

        Args:
            new_status: The desired new status.

        Raises:
            ProposalStateError: If the transition is invalid.
        """
        current = ProposalStatus(self.status)
        validate_transition(current, new_status)
        self.status = new_status.value
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_terminal(self) -> bool:
        """Check if the proposal is in a terminal state."""
        return is_terminal(ProposalStatus(self.status))

    @property
    def has_policy_decision(self) -> bool:
        """Check if this proposal has at least one PolicyDecision."""
        return self.decisions.exists()


class CounterProposal(models.Model):
    """
    Append-only record of a counter-offer generated in response to a proposal.

    CounterProposals are NEVER updated or deleted.

    Source: 03-DATA-MODEL.md Section 10.2
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="counter_proposals",
        help_text="The proposal being countered.",
    )
    sender = models.ForeignKey(
        "agents.Agent",
        on_delete=models.PROTECT,
        related_name="sent_counter_proposals",
        help_text="Agent that created this counter-proposal.",
    )
    adjustments = models.JSONField(
        help_text="What changed vs. original proposal.",
    )
    reasoning = models.TextField(
        default="",
        blank=True,
        help_text="LLM-generated explanation of the counter-offer.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Manager
    objects = AppendOnlyManager()

    class Meta:
        db_table = "legatio_proposals_counterproposal"
        verbose_name = "counter proposal"
        verbose_name_plural = "counter proposals"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"CounterProposal to {self.proposal.id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to prevent updates to existing records."""
        if self.pk and not self._state.adding:
            raise RuntimeError(
                "CounterProposal records are append-only. "
                "Cannot update an existing counter-proposal."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Prevent deletion of counter-proposals."""
        raise RuntimeError(
            "CounterProposal records are append-only. " "Cannot delete a counter-proposal."
        )


class PolicyDecision(models.Model):
    """
    The most critical append-only entity. Records every Policy Engine evaluation.

    PolicyDecisions are NEVER updated or deleted. They form the audit trail
    of all policy evaluations.

    Source: 03-DATA-MODEL.md Section 10.3
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="decisions",
        help_text="The proposal that was evaluated.",
    )
    constitution_version = models.ForeignKey(
        "constitutions.ConstitutionVersion",
        on_delete=models.PROTECT,
        related_name="policy_decisions",
        help_text="ConstitutionVersion used for evaluation.",
    )
    outcome = models.CharField(
        max_length=30,
        choices=PolicyDecisionOutcome.choices,
        help_text="The decision: ALLOW, DENY, REQUIRE_HUMAN_APPROVAL, or ERROR.",
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        help_text="Assessed risk level of the action.",
    )
    reason = models.TextField(
        help_text="Human-readable explanation of the decision.",
    )
    matched_rules = models.JSONField(
        default=list,
        blank=True,
        help_text="List of rules that matched during evaluation.",
    )
    evaluation_duration_ms = models.PositiveIntegerField(
        help_text="Time taken to evaluate in milliseconds.",
    )
    engine_version = models.CharField(
        max_length=20,
        help_text="Version of the Policy Engine that made the decision.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Manager
    objects = AppendOnlyManager()

    class Meta:
        db_table = "legatio_proposals_policydecision"
        verbose_name = "policy decision"
        verbose_name_plural = "policy decisions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["proposal"], name="idx_policydecision_proposal"),
            models.Index(fields=["outcome"], name="idx_policydecision_outcome"),
        ]

    def __str__(self) -> str:
        return f"PolicyDecision {self.id} ({self.outcome}) for {self.proposal.id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to prevent updates to existing records."""
        if self.pk and not self._state.adding:
            raise RuntimeError(
                "PolicyDecision records are append-only. "
                "Cannot update an existing policy decision."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Prevent deletion of policy decisions."""
        raise RuntimeError(
            "PolicyDecision records are append-only. " "Cannot delete a policy decision."
        )
