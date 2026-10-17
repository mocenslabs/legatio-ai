"""
Views for the constitutions app.

Exposes Constitution, ConstitutionVersion, and PolicyRule endpoints.
All endpoints enforce ownership isolation.

Source: 05-ROADMAP.md Section 6.5
"""

from typing import Any
from uuid import UUID

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.constitutions.models import Constitution, ConstitutionVersion, PolicyRule
from apps.constitutions.serializers import (
    ConstitutionActivateSerializer,
    ConstitutionCreateSerializer,
    ConstitutionSerializer,
    ConstitutionVersionSerializer,
    ConstitutionWithRulesSerializer,
    EvaluateRuleSerializer,
    PolicyRuleCreateSerializer,
    PolicyRuleSerializer,
    PolicyRuleUpdateSerializer,
)
from apps.constitutions.services import (
    activate_version,
    add_rule,
    create_constitution,
    create_constitution_with_rules,
    delete_rule,
    update_rule,
)
from core.permissions import IsOwner


class ConstitutionViewSet(ModelViewSet):  # type: ignore[type-arg]
    """
    ViewSet for Constitution CRUD.

    Endpoints:
        GET    /api/v1/constitutions/
        POST   /api/v1/constitutions/
        GET    /api/v1/constitutions/{id}/
        PATCH  /api/v1/constitutions/{id}/
        DELETE /api/v1/constitutions/{id}/
        POST   /api/v1/constitutions/{id}/activate
        GET    /api/v1/constitutions/{id}/versions
        POST   /api/v1/constitutions/{id}/with-rules/
    """

    queryset = Constitution.objects.all()
    serializer_class = ConstitutionSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    ordering = ["-created_at"]

    def get_queryset(self) -> Any:
        """Filter constitutions by owner via agent ownership chain."""
        queryset = Constitution.objects.all()
        if not hasattr(self, "request") or self.request is None:
            return queryset.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        return queryset.filter(agent__owner=user)

    def get_serializer_class(self) -> Any:
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return ConstitutionCreateSerializer
        if self.action == "with_rules":
            return ConstitutionWithRulesSerializer
        if self.action == "activate":
            return ConstitutionActivateSerializer
        return ConstitutionSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new Constitution."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.agents.models import Agent

        agent = Agent.objects.get(id=serializer.validated_data["agent_id"])
        constitution = create_constitution(
            agent=agent,
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description"),
            user=request.user,
        )

        return Response(
            ConstitutionSerializer(constitution, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update a Constitution's metadata."""
        constitution = self.get_object()

        from apps.constitutions.services import update_constitution

        try:
            constitution = update_constitution(
                constitution=constitution,
                name=request.data.get("name"),
                description=request.data.get("description"),
                user=request.user,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ConstitutionSerializer(constitution, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Soft-delete a Constitution."""
        constitution = self.get_object()
        constitution.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request: Request, pk: UUID | None = None) -> Response:
        """
        Activate a specific version of the Constitution.

        POST /api/v1/constitutions/{id}/activate
        Body: {"version_id": "uuid"}
        """
        constitution = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version_id = serializer.validated_data["version_id"]
        replace_active = bool(serializer.validated_data.get("replace_active", False))
        try:
            version = constitution.versions.get(id=version_id)
        except ConstitutionVersion.DoesNotExist:
            return Response(
                {"error": "Version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            activated_version = activate_version(
                version=version,
                user=request.user,
                replace_active=replace_active,
            )
        except Exception as exc:
            err_code = getattr(exc, "code", None) or exc.__class__.__name__
            return Response(
                {
                    "error": str(exc),
                    "code": err_code,
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        constitution.refresh_from_db()
        return Response(
            {
                "constitution": ConstitutionSerializer(
                    constitution, context={"request": request}
                ).data,
                "activated_version": ConstitutionVersionSerializer(activated_version).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="versions")
    def versions(self, request: Request, pk: UUID | None = None) -> Response:
        """
        List all versions of a Constitution.

        GET /api/v1/constitutions/{id}/versions
        """
        constitution = self.get_object()
        versions = constitution.versions.order_by("-version_number")
        serializer = ConstitutionVersionSerializer(versions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="with-rules")
    def with_rules(self, request: Request) -> Response:
        """
        Create a Constitution with rules in one atomic call.

        POST /api/v1/constitutions/{id}/with-rules/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.agents.models import Agent

        agent = Agent.objects.get(id=serializer.validated_data["agent_id"])

        try:
            constitution, version = create_constitution_with_rules(
                agent=agent,
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description"),
                rules=serializer.validated_data["rules"],
                user=request.user,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "constitution": ConstitutionSerializer(
                    constitution, context={"request": request}
                ).data,
                "version": ConstitutionVersionSerializer(version).data,
                "rules_count": version.rules.count(),
            },
            status=status.HTTP_201_CREATED,
        )


class PolicyRuleViewSet(ModelViewSet):  # type: ignore[type-arg]
    """
    ViewSet for PolicyRule CRUD.

    Endpoints:
        POST   /api/v1/constitutions/{constitution_id}/rules/
        PATCH  /api/v1/rules/{id}/
        DELETE /api/v1/rules/{id}/
        POST   /api/v1/rules/{id}/evaluate
    """

    queryset = PolicyRule.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> Any:
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return PolicyRuleCreateSerializer
        if self.action == "partial_update":
            return PolicyRuleUpdateSerializer
        if self.action == "evaluate":
            return EvaluateRuleSerializer
        return PolicyRuleSerializer

    def get_queryset(self) -> Any:
        """Filter rules by constitution ownership."""
        queryset = super().get_queryset()
        # Filter by constitution → agent → owner
        if not hasattr(self, "request") or self.request is None:
            return queryset.none()
        return queryset.filter(version__constitution__agent__owner=self.request.user)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Add a rule to a ConstitutionVersion.

        POST /api/v1/constitutions/{constitution_id}/rules/
        Body: {"version_id": "uuid", ...rule fields...}
        """
        constitution_id = kwargs.get("constitution_id")

        # Verify ownership
        try:
            constitution = Constitution.objects.get(
                id=constitution_id,
                agent__owner=request.user,
            )
        except Constitution.DoesNotExist:
            return Response(
                {"error": "Constitution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get version
        version_id = request.data.get("version_id")
        if not version_id:
            return Response(
                {"error": "version_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            version = constitution.versions.get(id=version_id)
        except ConstitutionVersion.DoesNotExist:
            return Response(
                {"error": "Version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            rule = add_rule(
                version=version,
                rule_number=serializer.validated_data["rule_number"],
                name=serializer.validated_data["name"],
                category=serializer.validated_data["category"],
                field=serializer.validated_data["field"],
                operator=serializer.validated_data["operator"],
                value=serializer.validated_data["value"],
                action=serializer.validated_data.get("action", "DENY"),
                priority=serializer.validated_data.get("priority", 100),
                description=serializer.validated_data.get("description"),
                user=request.user,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PolicyRuleSerializer(rule).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a PolicyRule.

        PATCH /api/v1/rules/{id}/
        """
        rule = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            rule = update_rule(
                rule=rule,
                name=serializer.validated_data.get("name"),
                description=serializer.validated_data.get("description"),
                field=serializer.validated_data.get("field"),
                operator=serializer.validated_data.get("operator"),
                value=serializer.validated_data.get("value"),
                action=serializer.validated_data.get("action"),
                priority=serializer.validated_data.get("priority"),
                is_active=serializer.validated_data.get("is_active"),
                user=request.user,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PolicyRuleSerializer(rule).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a PolicyRule.

        DELETE /api/v1/rules/{id}/
        """
        rule = self.get_object()

        try:
            delete_rule(rule=rule, user=request.user)
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="evaluate")
    def evaluate(self, request: Request, pk: UUID | None = None) -> Response:
        """
        Test a rule against a proposed action (dry-run).

        POST /api/v1/rules/{id}/evaluate
        Body: {"action": {...ProposedAction fields...}}
        """
        rule = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from core.schemas.policy import ProposedAction, RuleCondition
        from services.policy_engine.evaluator import evaluate_condition
        from services.policy_engine.types import RuleInput

        # Build RuleInput from the rule
        rule_input = RuleInput(
            rule_id=str(rule.id),
            rule_number=rule.rule_number,
            name=rule.name,
            category=rule.category,
            action=rule.action,
            conditions=[
                RuleCondition(
                    field_name=rule.field,
                    operator=rule.operator,
                    value=rule.value,
                    category=rule.category,
                )
            ],
            is_active=rule.is_active,
        )

        # Build ProposedAction
        action_data = serializer.validated_data["action"]
        action = ProposedAction(**action_data)

        # Evaluate
        matches = evaluate_condition(rule_input.conditions[0], action)

        return Response(
            {
                "rule_id": str(rule.id),
                "rule_number": rule.rule_number,
                "rule_name": rule.name,
                "matches": matches,
                "action": action_data,
                "explanation": (
                    f"Rule #{rule.rule_number} ({rule.name}) "
                    f"{'MATCHES' if matches else 'does not match'} the proposed action."
                ),
            },
            status=status.HTTP_200_OK,
        )
