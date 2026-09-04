"""Automation Service layer.

This module provides a service for managing automation rules and processing
triggers. When a trigger fires, matching active rules are evaluated against
the event context, and their actions are executed.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from django.db import transaction

from apps.agents.models import ActionType, AutomationRule, TriggerType
from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.policies.engine.evaluator import safe_evaluate

logger = logging.getLogger(__name__)


class AutomationServiceError(Exception):
    """Base exception for automation service errors."""


class AutomationService:
    """Service layer for automation rule operations.

    Manages automation rule creation and trigger processing. When a
    trigger fires, the service finds all active rules matching the
    trigger type, evaluates their conditions against the event context,
    and executes the configured actions.
    """

    @staticmethod
    @transaction.atomic
    def create_rule(
        agent_id: uuid.UUID,
        name: str,
        trigger_type: str,
        action_type: str,
        created_by_id: uuid.UUID,
        condition: dict[str, Any] | None = None,
        action_config: dict[str, Any] | None = None,
        priority: int = 100,
    ) -> AutomationRule:
        """Create a new automation rule.

        Args:
            agent_id: The UUID of the agent that owns the rule.
            name: Human-readable name for the rule.
            trigger_type: The event that triggers the rule.
            action_type: The action the agent executes.
            created_by_id: The UUID of the user creating the rule.
            condition: Optional JSON condition for the rule.
            action_config: Optional JSON configuration for the action.
            priority: Priority for rule evaluation order.

        Returns:
            The created AutomationRule instance.

        Raises:
            AutomationServiceError: If types are invalid or agent not found.
        """
        from apps.agents.models import Agent

        valid_triggers = {choice.value for choice in TriggerType}
        if trigger_type not in valid_triggers:
            raise AutomationServiceError(f"Invalid trigger_type: {trigger_type}")

        valid_actions = {choice.value for choice in ActionType}
        if action_type not in valid_actions:
            raise AutomationServiceError(f"Invalid action_type: {action_type}")

        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist as e:
            raise AutomationServiceError(f"Agent {agent_id} not found") from e

        rule = AutomationRule.objects.create(
            agent=agent,
            name=name,
            trigger_type=trigger_type,
            action_type=action_type,
            condition=condition if condition is not None else {},
            action_config=action_config if action_config is not None else {},
            priority=priority,
            created_by_id=created_by_id,
        )

        AuditService.log_agent_event(
            action=AuditAction.AUTOMATION_RULE_CREATED,
            agent_id=agent.id,
            actor_id=created_by_id,
            new_state={"rule_id": str(rule.id), "name": rule.name},
            metadata={"trigger_type": trigger_type, "action_type": action_type},
        )

        return rule

    @staticmethod
    def process_trigger(
        trigger_type: str,
        context: dict[str, Any],
    ) -> list[AutomationRule]:
        """Process a trigger event and execute matching rules.

        Finds all active rules matching the trigger type, evaluates their
        conditions against the context, and executes actions for rules
        whose conditions are met.

        Args:
            trigger_type: The type of trigger that fired.
            context: Event context data for condition evaluation.

        Returns:
            List of rules that were executed.
        """
        rules = AutomationRule.objects.filter(
            trigger_type=trigger_type,
            is_active=True,
            agent__is_active=True,
        ).order_by("priority", "-created_at")

        executed_rules: list[AutomationRule] = []

        for rule in rules:
            try:
                if AutomationService._evaluate_rule_condition(rule, context):
                    AutomationService._execute_rule_action(rule, context)
                    executed_rules.append(rule)
            except Exception as e:
                # Fail-safe: log the error but continue with other rules
                logger.exception(
                    "Failed to execute automation rule %s: %s",
                    rule.id,
                    str(e),
                )

        return executed_rules

    @staticmethod
    def _evaluate_rule_condition(
        rule: AutomationRule,
        context: dict[str, Any],
    ) -> bool:
        """Evaluate a rule's condition against the context.

        Args:
            rule: The automation rule to evaluate.
            context: Event context data for evaluation.

        Returns:
            True if the condition is met or no condition is configured.
        """
        if not rule.has_condition:
            return True

        result = safe_evaluate(rule.condition, context)
        return bool(result.success and result.result)

    @staticmethod
    def _execute_rule_action(
        rule: AutomationRule,
        context: dict[str, Any],
    ) -> None:
        """Execute the action configured for a rule.

        Args:
            rule: The automation rule whose action to execute.
            context: Event context data for the action.
        """
        if rule.action_type == ActionType.NOTIFY:
            AutomationService._execute_notify(rule, context)
        elif rule.action_type == ActionType.ADD_COMMENT:
            AutomationService._execute_add_comment(rule, context)
        elif rule.action_type == ActionType.CREATE_PROPOSAL:
            AutomationService._execute_create_proposal(rule, context)
        else:
            logger.info(
                "Action type %s not yet implemented for rule %s",
                rule.action_type,
                rule.id,
            )

        # Record rule execution in audit log
        AuditService.log_agent_event(
            action=AuditAction.AUTOMATION_RULE_EXECUTED,
            agent_id=rule.agent_id,
            actor_id=rule.agent.created_by_id,
            metadata={
                "rule_id": str(rule.id),
                "trigger_type": rule.trigger_type,
                "action_type": rule.action_type,
            },
        )

    @staticmethod
    def _execute_notify(rule: AutomationRule, context: dict[str, Any]) -> None:
        """Execute a NOTIFY action.

        Args:
            rule: The automation rule.
            context: Event context data.
        """
        from apps.notifications.models import NotificationType
        from apps.notifications.services import NotificationService

        recipient_id = rule.action_config.get("recipient_id")
        if recipient_id is None:
            recipient_id = rule.agent.created_by_id

        NotificationService.notify_proposal_status(
            proposal_id=context.get("proposal_id", uuid.uuid4()),
            recipient_id=uuid.UUID(str(recipient_id)),
            notification_type=NotificationType.SYSTEM,
            title=rule.action_config.get("title", "Automated notification"),
            message=rule.action_config.get("message", "This notification was sent by an agent."),
        )

    @staticmethod
    def _execute_add_comment(rule: AutomationRule, context: dict[str, Any]) -> None:
        """Execute an ADD_COMMENT action.

        Args:
            rule: The automation rule.
            context: Event context data.
        """
        from apps.negotiations.services import CommentService

        entity_type = context.get("entity_type")
        entity_id = context.get("entity_id")
        content = rule.action_config.get("content", "Automated comment from agent.")

        if entity_type is None or entity_id is None:
            logger.warning(
                "ADD_COMMENT action skipped: missing entity_type or entity_id in context"
            )
            return

        CommentService.add_comment(
            entity_type=entity_type,
            entity_id=uuid.UUID(str(entity_id)),
            author_id=rule.agent.created_by_id,
            content=content,
        )

    @staticmethod
    def _execute_create_proposal(rule: AutomationRule, context: dict[str, Any]) -> None:
        """Execute a CREATE_PROPOSAL action.

        Args:
            rule: The automation rule.
            context: Event context data.
        """
        from apps.proposals.services import ProposalService

        title = rule.action_config.get("title", "Automated proposal")
        action_type = rule.action_config.get("action_type", "AUTOMATED_ACTION")
        target_resource = rule.action_config.get("target_resource", "automated")
        payload = rule.action_config.get("payload", {})

        ProposalService.create_proposal(
            title=title,
            action_type=action_type,
            target_resource=target_resource,
            payload=payload,
            created_by_id=rule.agent.created_by_id,
        )

    @staticmethod
    def execute_rule(
        rule_id: uuid.UUID,
        context: dict[str, Any],
    ) -> bool:
        """Execute a specific automation rule against a context.

        Evaluates the rule's condition and executes its action if met.

        Args:
            rule_id: The UUID of the rule to execute.
            context: Event context data for evaluation and action.

        Returns:
            True if the rule was executed, False if condition was not met.

        Raises:
            AutomationServiceError: If the rule doesn't exist or can't fire.
        """
        try:
            rule = AutomationRule.objects.get(id=rule_id)
        except AutomationRule.DoesNotExist as e:
            raise AutomationServiceError(f"Rule {rule_id} not found") from e

        if not rule.can_fire:
            raise AutomationServiceError(f"Rule {rule_id} cannot fire (inactive)")

        if not AutomationService._evaluate_rule_condition(rule, context):
            return False

        AutomationService._execute_rule_action(rule, context)
        return True
