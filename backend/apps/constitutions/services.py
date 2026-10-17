"""
Business services for Constitution management.

Handles CRUD operations, version activation, and integration with Policy Engine.

Source: 04-BUSINESS-FLOW.md Section 8.5
Source: 03-DATA-MODEL.md Section 17.3
"""

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.services import create_audit_event
from apps.constitutions.models import Constitution, ConstitutionVersion, PolicyRule
from apps.constitutions.validators import (
    ConstitutionValidator,
    RuleSetValidator,
    RuleValidator,
)
from core.enums import (
    ActorType,
    ConstitutionStatus,
    EventType,
    RuleAction,
    RuleCategory,
    RuleOperator,
)
from core.exceptions import (
    ConstitutionImmutableError,
    MultipleActiveConstitutionsError,
)

logger = logging.getLogger("legatio.constitutions")


def create_constitution(
    *,
    agent: Any,
    name: str,
    description: str | None = None,
    user: Any,
) -> Constitution:
    """
    Create a new Constitution in DRAFT status.

    Args:
        agent: The agent that owns this constitution.
        name: Human-readable name.
        description: Optional description.
        user: The user creating the constitution (for audit).

    Returns:
        The created Constitution.

    Raises:
        ValueError: If validation fails.
    """
    # Validate input
    validator = ConstitutionValidator(name=name, description=description)

    constitution = Constitution.objects.create(
        agent=agent,
        name=validator.name,
        description=validator.description or "",
        status=ConstitutionStatus.DRAFT,
    )

    # Initial draft version so activate / rules always have a target
    create_version(constitution=constitution, user=user)

    # Audit event
    create_audit_event(
        event_type=EventType.CONSTITUTION_CREATED,
        actor_type=ActorType.USER,
        actor_id=user.id,
        entity_type="Constitution",
        entity_id=constitution.id,
        payload={
            "name": constitution.name,
            "agent_id": str(agent.id),
        },
    )

    logger.info(f"Constitution created: {constitution.id}")
    return constitution  # type: ignore[no-any-return]


def update_constitution(
    *,
    constitution: Constitution,
    name: str | None = None,
    description: str | None = None,
    user: Any,
) -> Constitution:
    """
    Update a Constitution's metadata.

    Args:
        constitution: The constitution to update.
        name: New name (optional).
        description: New description (optional).
        user: The user making the change (for audit).

    Returns:
        The updated Constitution.

    Raises:
        ConstitutionImmutableError: If constitution is ACTIVE or ARCHIVED.
    """
    if constitution.status in (ConstitutionStatus.ACTIVE, ConstitutionStatus.ARCHIVED):
        raise ConstitutionImmutableError(
            f"Constitution {constitution.id} is {constitution.status} and cannot be modified"
        )

    if name is not None:
        constitution.name = name
    if description is not None:
        constitution.description = description or ""

    constitution.save(update_fields=["name", "description", "updated_at"])

    logger.info(f"Constitution updated: {constitution.id}")
    return constitution


def create_version(
    *,
    constitution: Constitution,
    user: Any,
) -> ConstitutionVersion:
    """
    Create a new version for a Constitution.

    The version number is automatically incremented.

    Args:
        constitution: The constitution to create a version for.
        user: The user creating the version.

    Returns:
        The created ConstitutionVersion.
    """
    # Get next version number
    last_version = constitution.versions.order_by("-version_number").first()
    next_version_number = (last_version.version_number + 1) if last_version else 1

    version = ConstitutionVersion.objects.create(
        constitution=constitution,
        version_number=next_version_number,
        status=ConstitutionStatus.DRAFT,
        created_by=user,
    )

    logger.info(f"ConstitutionVersion created: {version.id} (v{version.version_number})")
    return version  # type: ignore[no-any-return]


def add_rule(
    *,
    version: ConstitutionVersion,
    rule_number: int,
    name: str,
    category: str | RuleCategory,
    field: str,
    operator: str | RuleOperator,
    value: Any,
    action: str | RuleAction = "DENY",
    priority: int = 100,
    description: str | None = None,
    user: Any,
) -> PolicyRule:
    """
    Add a rule to a ConstitutionVersion.

    Args:
        version: The version to add the rule to.
        rule_number: Display number for the rule.
        name: Human-readable name.
        category: Rule category (FINANCIAL, PRIVACY, etc.).
        field: Field to evaluate.
        operator: Comparison operator.
        value: Value to compare against.
        action: Action to take (ALLOW, DENY, REQUIRE_APPROVAL).
        priority: Evaluation priority (lower = first).
        description: Optional description.
        user: The user adding the rule (for audit).

    Returns:
        The created PolicyRule.

    Raises:
        ValueError: If validation fails.
        ConstitutionImmutableError: If version is ACTIVE or ARCHIVED.
    """
    # Check immutability
    if version.status in (ConstitutionStatus.ACTIVE, ConstitutionStatus.ARCHIVED):
        raise ConstitutionImmutableError(
            f"Version {version.id} is {version.status} and cannot be modified"
        )

    # Convert string values to enums if needed
    category_val = RuleCategory(category) if isinstance(category, str) else category
    operator_val = RuleOperator(operator) if isinstance(operator, str) else operator
    action_val = RuleAction(action) if isinstance(action, str) else action

    # Validate rule
    validator = RuleValidator(
        rule_number=rule_number,
        name=name,
        description=description,
        category=category_val,
        field=field,
        operator=operator_val,
        value=value,
        action=action_val,
        priority=priority,
    )

    rule = PolicyRule.objects.create(
        version=version,
        rule_number=validator.rule_number,
        name=validator.name,
        description=validator.description or "",
        category=validator.category,
        field=validator.field,
        operator=validator.operator,
        value=validator.value,
        action=validator.action,
        priority=validator.priority,
        is_active=validator.is_active,
    )

    # Audit event
    create_audit_event(
        event_type=EventType.CONSTITUTION_RULE_ADDED,
        actor_type=ActorType.USER,
        actor_id=user.id,
        entity_type="PolicyRule",
        entity_id=rule.id,
        payload={
            "version_id": str(version.id),
            "rule_number": rule.rule_number,
            "name": rule.name,
            "action": rule.action,
        },
    )

    logger.info(f"PolicyRule added: {rule.id} to version {version.id}")
    return rule


def update_rule(
    *,
    rule: PolicyRule,
    name: str | None = None,
    description: str | None = None,
    field: str | None = None,
    operator: str | None = None,
    value: Any = None,
    action: str | None = None,
    priority: int | None = None,
    is_active: bool | None = None,
    user: Any,
) -> PolicyRule:
    """
    Update a PolicyRule.

    Args:
        rule: The rule to update.
        name: New name (optional).
        description: New description (optional).
        field: New field (optional).
        operator: New operator (optional).
        value: New value (optional).
        action: New action (optional).
        priority: New priority (optional).
        is_active: New is_active status (optional).
        user: The user making the change (for audit).

    Returns:
        The updated PolicyRule.

    Raises:
        ConstitutionImmutableError: If the rule's version is ACTIVE or ARCHIVED.
    """
    # Check immutability
    if rule.version.status in (ConstitutionStatus.ACTIVE, ConstitutionStatus.ARCHIVED):
        raise ConstitutionImmutableError(
            f"Rule {rule.id} belongs to version {rule.version.id} which is {rule.version.status}"
        )

    # Update fields
    update_fields = []
    if name is not None:
        rule.name = name
        update_fields.append("name")
    if description is not None:
        rule.description = description or ""
        update_fields.append("description")
    if field is not None:
        rule.field = field
        update_fields.append("field")
    if operator is not None:
        rule.operator = operator
        update_fields.append("operator")
    if value is not None:
        rule.value = value
        update_fields.append("value")
    if action is not None:
        rule.action = action
        update_fields.append("action")
    if priority is not None:
        rule.priority = priority
        update_fields.append("priority")
    if is_active is not None:
        rule.is_active = is_active
        update_fields.append("is_active")

    if update_fields:
        rule.save(update_fields=update_fields)

    logger.info(f"PolicyRule updated: {rule.id}")
    return rule


def delete_rule(*, rule: PolicyRule, user: Any) -> None:
    """
    Delete a PolicyRule.

    Args:
        rule: The rule to delete.
        user: The user deleting the rule (for audit).

    Raises:
        ConstitutionImmutableError: If the rule's version is ACTIVE or ARCHIVED.
    """
    # Check immutability
    if rule.version.status in (ConstitutionStatus.ACTIVE, ConstitutionStatus.ARCHIVED):
        raise ConstitutionImmutableError(
            f"Rule {rule.id} belongs to version {rule.version.id} which is {rule.version.status}"
        )

    rule_id = rule.id
    rule.delete()

    logger.info(f"PolicyRule deleted: {rule_id}")


def activate_version(
    *,
    version: ConstitutionVersion,
    user: Any,
    replace_active: bool = False,
) -> ConstitutionVersion:
    """
    Activate a ConstitutionVersion.

    Atomic: optionally archive other active constitution on same agent,
    archive previous version, set this version ACTIVE, update constitution.

    Raises:
        MultipleActiveConstitutionsError: If another constitution is active
            and replace_active is False.
    """
    constitution = version.constitution

    with transaction.atomic():
        other_active = (
            Constitution.objects.filter(
                agent=constitution.agent,
                status=ConstitutionStatus.ACTIVE,
                deleted_at__isnull=True,
            )
            .exclude(id=constitution.id)
            .first()
        )

        if other_active:
            if not replace_active:
                raise MultipleActiveConstitutionsError(
                    f"Agent {constitution.agent.id} already has an active "
                    f"constitution: {other_active.id}"
                )
            if (
                other_active.active_version_id
                and other_active.active_version
                and other_active.active_version.status == ConstitutionStatus.ACTIVE
            ):
                prev_v = other_active.active_version
                prev_v.status = ConstitutionStatus.ARCHIVED
                prev_v.archived_at = timezone.now()
                prev_v.save(update_fields=["status", "archived_at"])
            other_active.status = ConstitutionStatus.ARCHIVED
            other_active.active_version = None
            other_active.save(update_fields=["status", "active_version", "updated_at"])
            logger.info(
                "Archived previous active constitution %s for agent %s",
                other_active.id,
                constitution.agent_id,
            )

        # Archive previous active version if exists
        if (
            constitution.active_version
            and constitution.active_version.status == ConstitutionStatus.ACTIVE
        ):
            previous_version = constitution.active_version
            previous_version.status = ConstitutionStatus.ARCHIVED
            previous_version.archived_at = timezone.now()
            previous_version.save(update_fields=["status", "archived_at"])
            logger.info(f"Previous version archived: {previous_version.id}")

        # Activate this version
        version.status = ConstitutionStatus.ACTIVE
        version.activated_at = timezone.now()
        version.save(update_fields=["status", "activated_at"])

        # Update constitution
        constitution.status = ConstitutionStatus.ACTIVE
        constitution.active_version = version
        constitution.save(update_fields=["status", "active_version", "updated_at"])

        # Audit event
        create_audit_event(
            event_type=EventType.CONSTITUTION_VERSION_ACTIVATED,
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="ConstitutionVersion",
            entity_id=version.id,
            payload={
                "constitution_id": str(constitution.id),
                "version_number": version.version_number,
            },
        )

        logger.info(f"ConstitutionVersion activated: {version.id}")

    return version


def create_constitution_with_rules(
    *,
    agent: Any,
    name: str,
    description: str | None,
    rules: list[dict[str, Any]],
    user: Any,
) -> tuple[Constitution, ConstitutionVersion]:
    """
    Create a Constitution with rules in one atomic operation.

    This is a convenience method for the Constitution Builder API.

    Args:
        agent: The agent that owns the constitution.
        name: Constitution name.
        description: Constitution description.
        rules: List of rule dictionaries.
        user: The user creating the constitution.

    Returns:
        Tuple of (Constitution, ConstitutionVersion).
    """
    with transaction.atomic():
        # Create constitution (also creates initial draft version v1)
        constitution = create_constitution(
            agent=agent,
            name=name,
            description=description,
            user=user,
        )

        # Reuse the initial draft version instead of creating v2 empty
        version = constitution.versions.order_by("version_number").first()
        if version is None:
            version = create_version(constitution=constitution, user=user)

        # Validate all rules
        rule_validator = RuleSetValidator(rules=[RuleValidator(**r) for r in rules])

        # Add rules
        for rule_data in rule_validator.rules:
            add_rule(
                version=version,
                rule_number=rule_data.rule_number,
                name=rule_data.name,
                category=rule_data.category.value,
                field=rule_data.field,
                operator=rule_data.operator.value,
                value=rule_data.value,
                action=rule_data.action.value,
                priority=rule_data.priority,
                description=rule_data.description,
                user=user,
            )

        logger.info(f"Constitution with {len(rules)} rules created: {constitution.id}")

    return constitution, version
