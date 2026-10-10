"""
Canonical JSON serialization for agreements.

Ensures deterministic JSON output: same input always produces the same
byte-for-byte JSON string, which is critical for hash verification.

Rules (from 04-BUSINESS-FLOW.md Section 10.1):
1. Keys sorted alphabetically at every level.
2. No extra whitespace (no pretty-printing).
3. Consistent number formatting (no trailing zeros).
4. UTF-8 encoding.
5. Null values represented as 'null'.
6. Booleans as 'true'/'false' (lowercase).

Source: 04-BUSINESS-FLOW.md Section 10.1
"""

import json
from decimal import Decimal
from typing import Any


class CanonicalEncoder(json.JSONEncoder):
    """
    JSON encoder that produces canonical (deterministic) output.

    Handles Decimal, UUID, datetime, and other types that the
    standard encoder doesn't support natively.
    """

    def default(self, obj: Any) -> Any:
        """Handle non-standard types."""
        if isinstance(obj, Decimal):
            # Normalize: remove trailing zeros
            return float(obj.normalize())
        if hasattr(obj, "isoformat"):
            # datetime, date, time
            return obj.isoformat()
        if hasattr(obj, "hex"):
            # UUID
            return str(obj)
        return super().default(obj)


def to_canonical_json(data: dict[str, Any]) -> str:
    """
    Serialize a dictionary to canonical JSON.

    Args:
        data: The data to serialize.

    Returns:
        A deterministic JSON string with sorted keys and no extra whitespace.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        cls=CanonicalEncoder,
    )


def to_canonical_bytes(data: dict[str, Any]) -> bytes:
    """
    Serialize a dictionary to canonical JSON bytes (UTF-8).

    Args:
        data: The data to serialize.

    Returns:
        UTF-8 encoded canonical JSON bytes.
    """
    return to_canonical_json(data).encode("utf-8")


def build_agreement_payload(
    *,
    proposal_id: str,
    room_id: str,
    constitution_version_id: str,
    action_type: str,
    amount: str | None,
    currency: str | None,
    terms: dict[str, Any],
    parties: list[dict[str, str]],
    user_agent_id: str,
    external_agent_id: str,
) -> dict[str, Any]:
    """
    Build the canonical payload for an agreement.

    This defines the exact structure that will be hashed and signed.
    All fields are included to ensure the signature covers the full agreement.

    Args:
        proposal_id: UUID of the accepted proposal.
        room_id: UUID of the negotiation room.
        constitution_version_id: UUID of the active constitution version.
        action_type: Type of action (e.g., 'purchase').
        amount: Monetary amount as string.
        currency: ISO 4217 currency code.
        terms: Full terms dictionary.
        parties: List of party dicts with 'id' and 'role'.
        user_agent_id: UUID of the user's agent.
        external_agent_id: UUID of the external agent.

    Returns:
        Dictionary ready for canonical serialization.
    """
    payload: dict[str, Any] = {
        "action_type": action_type,
        "constitution_version_id": constitution_version_id,
        "external_agent_id": external_agent_id,
        "parties": sorted(parties, key=lambda p: p["role"]),
        "proposal_id": proposal_id,
        "room_id": room_id,
        "terms": terms,
        "user_agent_id": user_agent_id,
    }
    # Only include amount and currency if present
    if amount is not None:
        payload["amount"] = amount
    if currency is not None:
        payload["currency"] = currency
    return payload


def generate_terms_summary(
    *,
    action_type: str,
    amount: str | None,
    currency: str | None,
    terms: dict[str, Any],
) -> str:
    """
    Generate a human-readable summary of the agreement terms.

    Args:
        action_type: Type of action.
        amount: Monetary amount.
        currency: Currency code.
        terms: Full terms dictionary.

    Returns:
        Human-readable summary string.
    """
    parts = []

    if action_type == "purchase":
        parts.append("Purchase")
        if terms.get("product"):
            parts.append(f"of {terms['product']}")
        if terms.get("destination"):
            parts.append(f"in {terms['destination']}")
        if terms.get("nights"):
            parts.append(f"for {terms['nights']} nights")
    elif action_type == "subscribe":
        parts.append("Subscription")
        if terms.get("service"):
            parts.append(f"for {terms['service']}")
        if terms.get("speed"):
            parts.append(f"at {terms['speed']}")
    else:
        parts.append(f"{action_type.capitalize()}")

    if amount and currency:
        parts.append(f"for {currency} {amount}")

    extra = []
    if terms.get("cancellation"):
        extra.append(f"{terms['cancellation']} cancellation")
    if terms.get("breakfast"):
        extra.append("breakfast included")
    if terms.get("auto_renewal") is False:
        extra.append("no auto-renewal")
    if extra:
        parts.append(f"({', '.join(extra)})")

    return " ".join(parts)
