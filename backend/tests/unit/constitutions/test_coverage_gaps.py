"""
Targeted tests for the lines of the constitutions module that the rest of the
suite does not reach (managers, serializers, views, loader, validators).

Every test documents which lines it exercises. No production code is modified.
"""

from types import SimpleNamespace
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.test import APIClient

from apps.agents.models import Agent
from apps.constitutions.managers import ConstitutionSoftDeleteQuerySet
from apps.constitutions.models import Constitution, ConstitutionVersion, PolicyRule
from apps.constitutions.serializers import (
    ConstitutionCreateSerializer,
    ConstitutionSerializer,
    ConstitutionWithRulesSerializer,
    EvaluateRuleSerializer,
    PolicyRuleCreateSerializer,
    PolicyRuleSerializer,
)
from apps.constitutions.services import (
    activate_version,
    add_rule,
    create_constitution,
    create_version,
    update_constitution,
)
from apps.constitutions.validators import RuleValidator
from apps.constitutions.views import ConstitutionViewSet, PolicyRuleViewSet
from core.enums import AgentType, ConstitutionStatus, RuleOperator
from core.exceptions import NoActiveConstitutionError
from services.policy_engine.loader import (
    get_active_constitution_version,
    load_active_rules_for_agent,
)

User = get_user_model()

RULE_PAYLOAD: dict[str, Any] = {
    "rule_number": 1,
    "name": "Max price",
    "category": "CUSTOM",
    "field": "price",
    "operator": "EQUALS",
    "value": "100",
    "action": "DENY",
    "priority": 100,
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _make_user(email: str) -> Any:
    return User.objects.create_user(email=email, password="pass1234")


def _make_agent(user: Any, name: str = "Agent") -> Agent:
    agent: Agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name=name)
    return agent


def _make_draft(user: Any, agent: Agent) -> tuple[Constitution, ConstitutionVersion, PolicyRule]:
    constitution = create_constitution(agent=agent, name="Const", user=user)
    version = create_version(constitution=constitution, user=user)
    rule = add_rule(
        version=version,
        rule_number=1,
        name="R1",
        category="CUSTOM",
        field="price",
        operator="EQUALS",
        value="100",
        user=user,
    )
    return constitution, version, rule


def _client(user: Any) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# --------------------------------------------------------------------------- #
# managers.py (lines 21, 31-36, 48, 65)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestManagerGaps:
    def test_queryset_dead_returns_only_soft_deleted(self) -> None:
        """managers.py line 21."""
        user = _make_user("mg1@x.com")
        agent = _make_agent(user)
        constitution = create_constitution(agent=agent, name="Gone", user=user)
        constitution.soft_delete()

        qs = ConstitutionSoftDeleteQuerySet(Constitution).filter(id=constitution.id)

        assert qs.dead().count() == 1
        assert qs.alive().count() == 0

    def test_queryset_delete_is_soft_by_default(self) -> None:
        """managers.py lines 31, 33, 35, 36 (soft delete branch)."""
        user = _make_user("mg2@x.com")
        agent = _make_agent(user)
        constitution = create_constitution(agent=agent, name="Soft", user=user)

        count, detail = (
            ConstitutionSoftDeleteQuerySet(Constitution).filter(id=constitution.id).delete()
        )

        assert count == 1
        assert detail == {Constitution._meta.label: 1}
        assert Constitution.all_objects.filter(id=constitution.id).exists()
        assert not Constitution.objects.filter(id=constitution.id).exists()

    def test_queryset_delete_hard_removes_rows(self) -> None:
        """managers.py lines 31-32 (hard delete branch)."""
        user = _make_user("mg3@x.com")
        agent = _make_agent(user)
        constitution = create_constitution(agent=agent, name="Hard", user=user)
        qs = ConstitutionSoftDeleteQuerySet(Constitution).filter(id=constitution.id)

        qs.delete(hard=True)

        assert not Constitution.all_objects.filter(id=constitution.id).exists()

    def test_manager_all_with_deleted(self) -> None:
        """managers.py line 48."""
        user = _make_user("mg4@x.com")
        agent = _make_agent(user)
        alive = create_constitution(agent=agent, name="Alive", user=user)
        dead = create_constitution(agent=agent, name="Dead", user=user)
        dead.soft_delete()

        ids = set(Constitution.objects.all_with_deleted().values_list("id", flat=True))

        assert {alive.id, dead.id} <= ids

    def test_immutable_queryset_update_allowed_on_draft(self) -> None:
        """managers.py line 65 (update passes through for DRAFT versions)."""
        user = _make_user("mg5@x.com")
        agent = _make_agent(user)
        constitution = create_constitution(agent=agent, name="Draft", user=user)
        version = create_version(constitution=constitution, user=user)

        updated = ConstitutionVersion.objects.filter(id=version.id).update(
            status=ConstitutionStatus.DRAFT
        )

        assert updated == 1


# --------------------------------------------------------------------------- #
# models.py (lines 212, 302)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestModelOwnerProperties:
    def test_version_and_rule_owner(self) -> None:
        """models.py lines 212 and 302."""
        user = _make_user("mo1@x.com")
        agent = _make_agent(user)
        _, version, rule = _make_draft(user, agent)

        assert version.owner == user
        assert rule.owner == user


# --------------------------------------------------------------------------- #
# serializers.py (67-68, 93-94, 183, 190-192, 244, 264-265)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestSerializerGaps:
    def test_policy_rule_serializer_wraps_validator_errors(self) -> None:
        """serializers.py lines 67-68."""
        # validate() is called directly: through is_valid() the ModelSerializer
        # would first demand the "version" FK, hiding the Pydantic error path.
        attrs = {**RULE_PAYLOAD, "field": "bad field!"}  # space and '!' are rejected
        with pytest.raises(serializers.ValidationError):
            PolicyRuleSerializer().validate(attrs)

    def test_policy_rule_create_serializer_wraps_validator_errors(self) -> None:
        """serializers.py lines 93-94."""
        serializer = PolicyRuleCreateSerializer(data={**RULE_PAYLOAD, "field": "bad field!"})
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_constitution_serializer_rejects_foreign_agent(self) -> None:
        """serializers.py line 183."""
        owner = _make_user("se1@x.com")
        intruder = _make_user("se2@x.com")
        agent = _make_agent(owner)
        serializer = ConstitutionSerializer(context={"request": SimpleNamespace(user=intruder)})

        with pytest.raises(serializers.ValidationError):
            serializer.validate_agent(agent)

    def test_constitution_serializer_validate_name(self) -> None:
        """serializers.py lines 190-192."""
        serializer = ConstitutionSerializer()

        with pytest.raises(serializers.ValidationError):
            serializer.validate_name("   ")
        assert serializer.validate_name("  Trimmed  ") == "Trimmed"

    def test_with_rules_serializer_rejects_foreign_agent(self) -> None:
        """serializers.py line 244."""
        owner = _make_user("se3@x.com")
        intruder = _make_user("se4@x.com")
        agent = _make_agent(owner)
        serializer = ConstitutionWithRulesSerializer(
            context={"request": SimpleNamespace(user=intruder)}
        )

        with pytest.raises(serializers.ValidationError):
            serializer.validate_agent_id(str(agent.id))

    def test_create_serializer_rejects_foreign_agent(self) -> None:
        """Companion check for ConstitutionCreateSerializer.validate_agent_id."""
        owner = _make_user("se5@x.com")
        intruder = _make_user("se6@x.com")
        agent = _make_agent(owner)
        serializer = ConstitutionCreateSerializer(
            context={"request": SimpleNamespace(user=intruder)}
        )

        with pytest.raises(serializers.ValidationError):
            serializer.validate_agent_id(str(agent.id))

    def test_evaluate_serializer_rejects_invalid_action(self) -> None:
        """serializers.py lines 264-265."""
        serializer = EvaluateRuleSerializer(data={"action": {"not_a_field": 1}})
        assert not serializer.is_valid()
        assert "action" in serializer.errors


# --------------------------------------------------------------------------- #
# services.py (115-123)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestUpdateConstitutionSuccess:
    def test_update_name_and_description(self) -> None:
        """services.py lines 115-123."""
        user = _make_user("sv1@x.com")
        agent = _make_agent(user)
        constitution = create_constitution(agent=agent, name="Old", user=user)

        updated = update_constitution(
            constitution=constitution, name="New", description="Desc", user=user
        )
        assert updated.name == "New"
        assert updated.description == "Desc"

        cleared = update_constitution(constitution=updated, description="", user=user)
        assert cleared.description == ""
        assert cleared.name == "New"


# --------------------------------------------------------------------------- #
# validators.py (42, 55, 70)
# --------------------------------------------------------------------------- #
class TestValidatorGaps:
    def test_blank_field_name_rejected(self) -> None:
        """validators.py line 42."""
        with pytest.raises(ValueError, match="Field name cannot be empty"):
            RuleValidator(**{**RULE_PAYLOAD, "field": "   "})

    def test_none_value_rejected(self) -> None:
        """validators.py line 55."""
        with pytest.raises(ValueError, match="Value cannot be None"):
            RuleValidator(**{**RULE_PAYLOAD, "value": None})

    def test_contains_operator_coerces_value_to_str(self) -> None:
        """validators.py line 70."""
        rule = RuleValidator(**{**RULE_PAYLOAD, "operator": RuleOperator.CONTAINS, "value": 42})
        assert rule.value == "42"


# --------------------------------------------------------------------------- #
# loader.py (76, 105-106, 110-111)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestLoaderGaps:
    def test_get_active_version_success(self) -> None:
        """loader.py lines 110-111."""
        user = _make_user("lo1@x.com")
        agent = _make_agent(user)
        _, version, _ = _make_draft(user, agent)
        activate_version(version=version, user=user)

        assert get_active_constitution_version(agent).id == version.id

    def test_get_active_version_without_active_constitution(self) -> None:
        """loader.py first guard of get_active_constitution_version."""
        agent = _make_agent(_make_user("lo2@x.com"))
        with pytest.raises(NoActiveConstitutionError):
            get_active_constitution_version(agent)

    def test_active_constitution_without_active_version(self) -> None:
        """loader.py lines 76 and 105-106."""
        user = _make_user("lo3@x.com")
        agent = _make_agent(user)
        constitution = create_constitution(agent=agent, name="Broken", user=user)
        Constitution.all_objects.filter(id=constitution.id).update(
            status=ConstitutionStatus.ACTIVE, active_version=None
        )

        with pytest.raises(NoActiveConstitutionError, match="no active version"):
            load_active_rules_for_agent(agent)
        with pytest.raises(NoActiveConstitutionError, match="no active version"):
            get_active_constitution_version(agent)


# --------------------------------------------------------------------------- #
# views.py
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestViewQuerysetGuards:
    def test_constitution_viewset_queryset_without_request(self) -> None:
        """views.py line 67."""
        assert ConstitutionViewSet().get_queryset().count() == 0

    def test_constitution_viewset_queryset_unauthenticated(self) -> None:
        """views.py line 70."""
        view = ConstitutionViewSet()
        view.request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))  # type: ignore[assignment]
        assert view.get_queryset().count() == 0

    def test_rule_viewset_queryset_without_request(self) -> None:
        """views.py line 254."""
        assert PolicyRuleViewSet().get_queryset().count() == 0

    def test_rule_viewset_default_serializer_class(self) -> None:
        """views.py line 247."""
        view = PolicyRuleViewSet()
        view.action = "retrieve"
        assert view.get_serializer_class() is PolicyRuleSerializer


@pytest.mark.django_db
class TestConstitutionViewGaps:
    def test_patch_and_delete_constitution(self) -> None:
        """views.py lines 122 and 129-131."""
        user = _make_user("vw1@x.com")
        agent = _make_agent(user)
        constitution = create_constitution(agent=agent, name="Orig", user=user)
        client = _client(user)

        patch = client.patch(
            f"/api/v1/constitutions/{constitution.id}/", {"name": "Renamed"}, format="json"
        )
        assert patch.status_code == 200
        assert patch.data["name"] == "Renamed"

        delete = client.delete(f"/api/v1/constitutions/{constitution.id}/")
        assert delete.status_code == 204
        assert not Constitution.objects.filter(id=constitution.id).exists()
        assert Constitution.all_objects.filter(id=constitution.id).exists()

    def test_activate_unknown_version_returns_404(self) -> None:
        """views.py lines 148-149."""
        user = _make_user("vw2@x.com")
        agent = _make_agent(user)
        constitution, _, _ = _make_draft(user, agent)
        other_constitution = create_constitution(agent=_make_agent(user, "B"), name="B", user=user)
        foreign_version = create_version(constitution=other_constitution, user=user)

        response = _client(user).post(
            f"/api/v1/constitutions/{constitution.id}/activate/",
            {"version_id": str(foreign_version.id)},
            format="json",
        )
        assert response.status_code == 404

    def test_activate_blocked_when_agent_has_another_active_constitution(self) -> None:
        """views.py lines 156-157."""
        user = _make_user("vw3@x.com")
        agent = _make_agent(user)
        _, version_a, _ = _make_draft(user, agent)
        activate_version(version=version_a, user=user)
        constitution_b, version_b, _ = _make_draft(user, agent)

        response = _client(user).post(
            f"/api/v1/constitutions/{constitution_b.id}/activate/",
            {"version_id": str(version_b.id)},
            format="json",
        )
        assert response.status_code == 400
        assert "error" in response.data

    def test_with_rules_service_error_returns_400(self) -> None:
        """views.py lines 207-208 (duplicate rule numbers rejected by the service)."""
        user = _make_user("vw4@x.com")
        agent = _make_agent(user)
        # Individually valid rules that share a rule_number: only the service
        # layer (RuleSetValidator) rejects the set as a whole.
        rules = [RULE_PAYLOAD, {**RULE_PAYLOAD, "name": "Duplicate number"}]

        response = _client(user).post(
            "/api/v1/constitutions/with-rules/",
            {"agent_id": str(agent.id), "name": "Bad", "rules": rules},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestRuleViewGaps:
    def test_create_rule_without_version_id_returns_400(self) -> None:
        """views.py line 284."""
        user = _make_user("vw5@x.com")
        agent = _make_agent(user)
        constitution, _, _ = _make_draft(user, agent)

        response = _client(user).post(
            f"/api/v1/constitutions/{constitution.id}/rules/",
            {**RULE_PAYLOAD, "rule_number": 2},
            format="json",
        )
        assert response.status_code == 400
        assert response.data["error"] == "version_id is required."

    def test_patch_rule_of_active_version_returns_400(self) -> None:
        """views.py lines 345-346."""
        user = _make_user("vw6@x.com")
        agent = _make_agent(user)
        _, version, rule = _make_draft(user, agent)
        activate_version(version=version, user=user)

        response = _client(user).patch(
            f"/api/v1/rules/{rule.id}/", {"name": "Hacked"}, format="json"
        )
        assert response.status_code == 400

    def test_delete_rule_of_active_version_returns_400(self) -> None:
        """views.py lines 366-367."""
        user = _make_user("vw7@x.com")
        agent = _make_agent(user)
        _, version, rule = _make_draft(user, agent)
        activate_version(version=version, user=user)

        response = _client(user).delete(f"/api/v1/rules/{rule.id}/")
        assert response.status_code == 400
        assert PolicyRule.objects.filter(id=rule.id).exists()
