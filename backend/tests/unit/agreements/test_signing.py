"""
Unit tests for cryptographic signing and verification.
Source: 04-BUSINESS-FLOW.md Section 10.2 and 10.3
"""

from apps.agreements.signing import (
    compute_hash,
    sign_agreement_data,
    sign_payload,
    verify_signature,
)


class TestComputeHash:
    def test_deterministic(self) -> None:
        """Same input produces same hash."""
        data = {"amount": "700", "currency": "EUR"}
        h1 = compute_hash(data)
        h2 = compute_hash(data)
        assert h1 == h2

    def test_different_input_different_hash(self) -> None:
        """Different input produces different hash."""
        h1 = compute_hash({"amount": "700"})
        h2 = compute_hash({"amount": "800"})
        assert h1 != h2

    def test_hash_is_sha256_hex(self) -> None:
        """Hash is a valid SHA-256 hex string."""
        h = compute_hash({"test": "data"})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_key_order_irrelevant(self) -> None:
        """Key order doesn't affect hash (canonical sorting)."""
        h1 = compute_hash({"a": 1, "b": 2})
        h2 = compute_hash({"b": 2, "a": 1})
        assert h1 == h2


class TestSignPayload:
    def test_sign_produces_hex_string(self) -> None:
        """Signature is a hex string."""
        sig = sign_payload("abc123")
        assert len(sig) == 64
        assert all(c in "0123456789abcdef" for c in sig)

    def test_sign_deterministic(self) -> None:
        """Same hash produces same signature."""
        sig1 = sign_payload("abc123")
        sig2 = sign_payload("abc123")
        assert sig1 == sig2

    def test_different_hashes_different_signatures(self) -> None:
        """Different hashes produce different signatures."""
        sig1 = sign_payload("abc123")
        sig2 = sign_payload("def456")
        assert sig1 != sig2


class TestVerifySignature:
    def test_valid_signature(self) -> None:
        """Valid signature passes verification."""
        hash_val = compute_hash({"test": "data"})
        sig = sign_payload(hash_val)
        assert verify_signature(hash_val, sig) is True

    def test_invalid_signature(self) -> None:
        """Invalid signature fails verification."""
        hash_val = compute_hash({"test": "data"})
        assert verify_signature(hash_val, "invalid_signature") is False

    def test_tampered_hash_fails(self) -> None:
        """Tampered hash fails verification."""
        hash_val = compute_hash({"test": "data"})
        sig = sign_payload(hash_val)
        assert verify_signature("tampered_hash", sig) is False


class TestSignAgreementData:
    def test_full_pipeline(self) -> None:
        """Full pipeline produces consistent results."""
        data = {"amount": "700", "currency": "EUR", "action": "purchase"}
        canonical_json, canonical_hash, signature = sign_agreement_data(data)
        assert isinstance(canonical_json, str)
        assert len(canonical_hash) == 64
        assert len(signature) == 64
        # Verify the signature
        assert verify_signature(canonical_hash, signature) is True

    def test_pipeline_deterministic(self) -> None:
        """Full pipeline is deterministic."""
        data = {"amount": "700", "currency": "EUR"}
        results = [sign_agreement_data(data) for _ in range(10)]
        hashes = [r[1] for r in results]
        sigs = [r[2] for r in results]
        assert len(set(hashes)) == 1
        assert len(set(sigs)) == 1
