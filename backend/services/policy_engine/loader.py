"""
Loader for Policy Engine rules from ConstitutionVersion.

Converts Django PolicyRule models to RuleInput for the Policy Engine.

Source: 02-ARCHITECTURE.md Section 8.1
"""

from typing import Any

from apps.constitutions.models import Constitution, ConstitutionVersion
from core.enums import RuleAction, RuleCategory, RuleOperator
from core.exceptions import NoActiveConstitutionError
from core.schemas.policy import RuleCondition
from services.policy_engine.types import RuleInput


def load_rules_from_version(version: ConstitutionVersion) -> list[RuleInput]:
    """
    Load all active rules from a ConstitutionVersion and convert to RuleInput.

    Args:
        version: The ConstitutionVersion to load rules from.

    Returns:
        List of RuleInput objects ready for Policy Engine evaluation.
    """
    rules = version.rules.filter(is_active=True).order_by("priority", "rule_number")

    return [
        RuleInput(
            rule_id=str(rule.id),
            rule_number=rule.rule_number,
            name=rule.name,
            category=RuleCategory(rule.category),
            action=RuleAction(rule.action),
            conditions=[
                RuleCondition(
                    field_name=rule.field,
                    operator=RuleOperator(rule.operator),
                    value=rule.value,
                )
            ],
            is_active=rule.is_active,
        )
        for rule in rules
    ]


def load_active_rules_for_agent(agent: Any) -> list[RuleInput]:
    """
    Load active rules from the agent's active Constitution.

    Args:
        agent: The Agent instance.

    Returns:
        List of RuleInput objects.

    Raises:
        NoActiveConstitutionError: If the agent has no active constitution.
    """
    # Find active constitution for this agent
    active_constitution = Constitution.objects.filter(
        agent=agent,
        status="ACTIVE",
        deleted_at__isnull=True,
    ).first()

    if not active_constitution:
        raise NoActiveConstitutionError(f"Agent {agent.id} has no active constitution")

    # Load active version
    if not active_constitution.active_version:
        raise NoActiveConstitutionError(
            f"Constitution {active_constitution.id} has no active version"
        )

    return load_rules_from_version(active_constitution.active_version)


def get_active_constitution_version(agent: Any) -> ConstitutionVersion:
    """
    Get the active ConstitutionVersion for an agent.

    Args:
        agent: The Agent instance.

    Returns:
        The active ConstitutionVersion.

    Raises:
        NoActiveConstitutionError: If no active constitution exists.
    """
    active_constitution = Constitution.objects.filter(
        agent=agent,
        status="ACTIVE",
        deleted_at__isnull=True,
    ).first()

    if not active_constitution:
        raise NoActiveConstitutionError(f"Agent {agent.id} has no active constitution")

    if not active_constitution.active_version:
        raise NoActiveConstitutionError(
            f"Constitution {active_constitution.id} has no active version"
        )

    version: ConstitutionVersion = active_constitution.active_version
    return version
