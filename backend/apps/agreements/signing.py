"""
Cryptographic signing and verification for agreements.

Uses HMAC-SHA256 with the server signing key for MVP.

Source: 04-BUSINESS-FLOW.md Section 10.3
"""

import hashlib
import hmac
from typing import Any

from django.conf import settings

from apps.agreements.canonical import to_canonical_bytes


def compute_hash(data: dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of canonical JSON representation.

    Args:
        data: The data to hash.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    canonical_bytes = to_canonical_bytes(data)
    return hashlib.sha256(canonical_bytes).hexdigest()


def sign_payload(canonical_hash: str) -> str:
    """
    Sign a canonical hash using HMAC-SHA256 with the server signing key.

    Args:
        canonical_hash: The SHA-256 hash of the canonical JSON.

    Returns:
        Hexadecimal HMAC-SHA256 signature string.
    """
    signing_key = settings.SERVER_SIGNING_KEY.encode("utf-8")
    message = canonical_hash.encode("utf-8")
    signature = hmac.new(
        key=signing_key,
        msg=message,
        digestmod=hashlib.sha256,
    )
    return signature.hexdigest()


def verify_signature(canonical_hash: str, signature: str) -> bool:
    """
    Verify an HMAC-SHA256 signature against a canonical hash.

    Args:
        canonical_hash: The SHA-256 hash of the canonical JSON.
        signature: The HMAC-SHA256 signature to verify.

    Returns:
        True if the signature is valid, False otherwise.
    """
    expected = sign_payload(canonical_hash)
    return hmac.compare_digest(expected, signature)


def sign_agreement_data(data: dict[str, Any]) -> tuple[str, str, str]:
    """
    Full signing pipeline: canonical JSON -> hash -> signature.

    Args:
        data: The agreement payload dictionary.

    Returns:
        Tuple of (canonical_json_string, canonical_hash, signature).
    """
    from apps.agreements.canonical import to_canonical_json

    canonical_json = to_canonical_json(data)
    canonical_hash = compute_hash(data)
    signature = sign_payload(canonical_hash)
    return canonical_json, canonical_hash, signature
