"""
Unit tests for canonical JSON serialization.
Source: 04-BUSINESS-FLOW.md Section 10.1
"""

import json
from decimal import Decimal

from apps.agreements.canonical import (
    build_agreement_payload,
    generate_terms_summary,
    to_canonical_bytes,
    to_canonical_json,
)


class TestCanonicalJSON:
    def test_sorted_keys(self) -> None:
        """Keys are sorted alphabetically."""
        data = {"z": 1, "a": 2, "m": 3}
        result = to_canonical_json(data)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_nested_sorted_keys(self) -> None:
        """Nested keys are also sorted."""
        data = {"b": {"z": 1, "a": 2}, "a": 3}
        result = to_canonical_json(data)
        assert result == '{"a":3,"b":{"a":2,"z":1}}'

    def test_no_extra_whitespace(self) -> None:
        """No spaces or newlines in output."""
        data = {"key": "value", "number": 42}
        result = to_canonical_json(data)
        assert " " not in result
        assert "\n" not in result

    def test_deterministic(self) -> None:
        """Same input always produces same output."""
        data = {"amount": "700", "currency": "EUR", "action": "purchase"}
        results = [to_canonical_json(data) for _ in range(100)]
        assert len(set(results)) == 1

    def test_decimal_handling(self) -> None:
        """Decimal values are normalized."""
        data = {"amount": Decimal("700.00")}
        result = to_canonical_json(data)
        parsed = json.loads(result)
        assert parsed["amount"] == 700.0

    def test_null_values(self) -> None:
        """None is serialized as null."""
        data = {"key": None}
        result = to_canonical_json(data)
        assert result == '{"key":null}'

    def test_boolean_values(self) -> None:
        """Booleans are lowercase."""
        data = {"active": True, "deleted": False}
        result = to_canonical_json(data)
        assert '"active":true' in result
        assert '"deleted":false' in result

    def test_utf8_encoding(self) -> None:
        """UTF-8 characters are preserved."""
        data = {"name": "Madrid 🇪🇸"}
        result = to_canonical_json(data)
        assert "Madrid 🇪🇸" in result

    def test_canonical_bytes_is_utf8(self) -> None:
        """to_canonical_bytes returns UTF-8 encoded bytes."""
        data = {"key": "value"}
        result = to_canonical_bytes(data)
        assert isinstance(result, bytes)
        assert result.decode("utf-8") == to_canonical_json(data)

    def test_empty_dict(self) -> None:
        """Empty dict produces empty JSON object."""
        assert to_canonical_json({}) == "{}"

    def test_list_values(self) -> None:
        """Lists preserve order (only keys are sorted)."""
        data = {"items": [3, 1, 2]}
        result = to_canonical_json(data)
        assert result == '{"items":[3,1,2]}'


class TestBuildAgreementPayload:
    def test_builds_complete_payload(self) -> None:
        """Payload includes all required fields."""
        payload = build_agreement_payload(
            proposal_id="prop-1",
            room_id="room-1",
            constitution_version_id="cv-1",
            action_type="purchase",
            amount="700.00",
            currency="EUR",
            terms={"nights": 5},
            parties=[
                {"id": "agent-1", "role": "buyer"},
                {"id": "agent-2", "role": "seller"},
            ],
            user_agent_id="agent-1",
            external_agent_id="agent-2",
        )
        assert payload["proposal_id"] == "prop-1"
        assert payload["amount"] == "700.00"
        assert payload["currency"] == "EUR"
        assert len(payload["parties"]) == 2

    def test_parties_sorted_by_role(self) -> None:
        """Parties are sorted by role."""
        payload = build_agreement_payload(
            proposal_id="p",
            room_id="r",
            constitution_version_id="cv",
            action_type="purchase",
            amount=None,
            currency=None,
            terms={},
            parties=[
                {"id": "a2", "role": "seller"},
                {"id": "a1", "role": "buyer"},
            ],
            user_agent_id="a1",
            external_agent_id="a2",
        )
        assert payload["parties"][0]["role"] == "buyer"
        assert payload["parties"][1]["role"] == "seller"

    def test_optional_fields_excluded(self) -> None:
        """Amount and currency excluded when None."""
        payload = build_agreement_payload(
            proposal_id="p",
            room_id="r",
            constitution_version_id="cv",
            action_type="share_data",
            amount=None,
            currency=None,
            terms={"fields": ["email"]},
            parties=[],
            user_agent_id="a1",
            external_agent_id="a2",
        )
        assert "amount" not in payload
        assert "currency" not in payload


class TestGenerateTermsSummary:
    def test_purchase_summary(self) -> None:
        """Purchase generates readable summary."""
        summary = generate_terms_summary(
            action_type="purchase",
            amount="700.00",
            currency="EUR",
            terms={"nights": 5, "destination": "Madrid"},
        )
        assert "Purchase" in summary
        assert "Madrid" in summary
        assert "5 nights" in summary
        assert "EUR 700.00" in summary

    def test_subscribe_summary(self) -> None:
        """Subscription generates readable summary."""
        summary = generate_terms_summary(
            action_type="subscribe",
            amount="70.00",
            currency="EUR",
            terms={"service": "internet", "speed": "600Mbps"},
        )
        assert "Subscription" in summary
        assert "internet" in summary
        assert "600Mbps" in summary
