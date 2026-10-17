"""
DRF serializers for the constitutions app.

Handles validation and serialization for Constitution, ConstitutionVersion,
and PolicyRule endpoints.

Source: 05-ROADMAP.md Section 6.5
"""

from typing import Any

from rest_framework import serializers

from apps.agents.models import Agent
from apps.constitutions.models import Constitution, ConstitutionVersion, PolicyRule
from apps.constitutions.validators import RuleValidator
from core.enums import ConstitutionStatus, RuleAction, RuleCategory, RuleOperator


class PolicyRuleSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for PolicyRule."""

    class Meta:
        model = PolicyRule
        fields = [
            "id",
            "version",
            "rule_number",
            "name",
            "description",
            "category",
            "field",
            "operator",
            "value",
            "action",
            "priority",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate rule using Pydantic validator."""
        # Get version from context if creating
        version = attrs.get("version") or self.context.get("version")

        # Check immutability
        if version and version.status in (
            ConstitutionStatus.ACTIVE,
            ConstitutionStatus.ARCHIVED,
        ):
            raise serializers.ValidationError(f"Cannot modify rules of a {version.status} version.")

        # Validate with Pydantic
        try:
            RuleValidator(
                rule_number=attrs.get("rule_number", 1),
                name=attrs.get("name", ""),
                description=attrs.get("description"),
                category=attrs.get("category", RuleCategory.CUSTOM),
                field=attrs.get("field", ""),
                operator=attrs.get("operator", RuleOperator.EQUALS),
                value=attrs.get("value"),
                action=attrs.get("action", RuleAction.DENY),
                priority=attrs.get("priority", 100),
            )
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc

        return attrs


class PolicyRuleCreateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for creating a PolicyRule."""

    rule_number = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=RuleCategory.choices)
    field = serializers.CharField(max_length=100)
    operator = serializers.ChoiceField(choices=RuleOperator.choices)
    value = serializers.JSONField()
    action = serializers.ChoiceField(
        choices=RuleAction.choices,
        default=RuleAction.DENY,
    )
    priority = serializers.IntegerField(default=100, min_value=1)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate using Pydantic."""
        try:
            RuleValidator(**attrs)
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return attrs


class PolicyRuleUpdateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for updating a PolicyRule."""

    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_null=True)
    field = serializers.CharField(max_length=100, required=False)
    operator = serializers.ChoiceField(choices=RuleOperator.choices, required=False)
    value = serializers.JSONField(required=False)
    action = serializers.ChoiceField(choices=RuleAction.choices, required=False)
    priority = serializers.IntegerField(min_value=1, required=False)
    is_active = serializers.BooleanField(required=False)


class ConstitutionVersionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for ConstitutionVersion (read-only)."""

    rules_count = serializers.SerializerMethodField()
    rules = PolicyRuleSerializer(many=True, read_only=True)

    class Meta:
        model = ConstitutionVersion
        fields = [
            "id",
            "constitution",
            "version_number",
            "status",
            "rules_snapshot",
            "created_by",
            "activated_at",
            "archived_at",
            "created_at",
            "rules_count",
            "rules",
        ]
        read_only_fields = fields

    def get_rules_count(self, obj: ConstitutionVersion) -> int:
        """Return the number of rules in this version."""
        return obj.rules.count()


class ConstitutionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for Constitution."""

    agent_name = serializers.CharField(source="agent.name", read_only=True)
    versions_count = serializers.SerializerMethodField()
    active_version_number = serializers.SerializerMethodField()

    class Meta:
        model = Constitution
        fields = [
            "id",
            "agent",
            "agent_name",
            "name",
            "description",
            "status",
            "active_version",
            "active_version_number",
            "versions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "active_version",
            "active_version_number",
            "versions_count",
            "created_at",
            "updated_at",
        ]

    def get_versions_count(self, obj: Constitution) -> int:
        """Return the number of versions."""
        return obj.versions.count()

    def get_active_version_number(self, obj: Constitution) -> int | None:
        """Return the active version number."""
        if obj.active_version:
            return obj.active_version.version_number
        return None

    def validate_agent(self, value: Agent) -> Agent:
        """Validate that the user owns the agent."""
        request = self.context.get("request")
        if request and hasattr(request, "user") and value.owner != request.user:
            raise serializers.ValidationError(
                "You can only create constitutions for your own agents."
            )
        return value

    def validate_name(self, value: str) -> str:
        """Validate constitution name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value.strip()


class ConstitutionCreateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for creating a Constitution."""

    agent_id = serializers.UUIDField()
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_agent_id(self, value: str) -> str:
        """Validate that the user owns the agent."""
        request = self.context.get("request")
        try:
            agent = Agent.objects.get(id=value)
        except Agent.DoesNotExist as exc:
            raise serializers.ValidationError("Agent not found.") from exc

        if request and hasattr(request, "user") and agent.owner != request.user:
            raise serializers.ValidationError(
                "You can only create constitutions for your own agents."
            )
        return value


class ConstitutionActivateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for activating a constitution version."""

    version_id = serializers.UUIDField()
    replace_active = serializers.BooleanField(required=False, default=False)


class ConstitutionWithRulesSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for creating a Constitution with rules in one call."""

    agent_id = serializers.UUIDField()
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    rules = serializers.ListField(
        child=PolicyRuleCreateSerializer(),
        min_length=1,
        max_length=100,
    )

    def validate_agent_id(self, value: str) -> str:
        """Validate that the user owns the agent."""
        request = self.context.get("request")
        try:
            agent = Agent.objects.get(id=value)
        except Agent.DoesNotExist as exc:
            raise serializers.ValidationError("Agent not found.") from exc

        if request and hasattr(request, "user") and agent.owner != request.user:
            raise serializers.ValidationError(
                "You can only create constitutions for your own agents."
            )
        return value


class EvaluateRuleSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for testing a rule against a proposal."""

    from core.schemas.policy import ProposedAction

    rule = PolicyRuleCreateSerializer(required=False)
    action = serializers.JSONField()

    def validate_action(self, value: dict[str, Any]) -> dict[str, Any]:
        """Validate the proposed action."""
        from core.schemas.policy import ProposedAction

        try:
            ProposedAction(**value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value
