"""
Unit tests for Credential model and services.

Source: 03-DATA-MODEL.md Section 7.2
"""

from typing import cast

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.agents.models import Agent, Credential
from apps.agents.services.credentials import (
    create_credential,
    generate_api_key,
    hash_api_key,
    revoke_credential,
    rotate_credential,
    verify_api_key,
)
from core.enums import AgentType


@pytest.fixture
def user() -> User:
    """Create a test user."""
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture
def agent(user: User) -> Agent:
    """Create a test agent."""
    return cast(
        Agent,
        Agent.objects.create(
            owner=user,
            agent_type=AgentType.USER_AGENT,
            name="Test Agent",
        ),
    )


@pytest.mark.django_db
class TestCredentialModel:
    """Tests for the Credential model."""

    def test_create_credential(self, user: User, agent: Agent) -> None:
        """Credential can be created."""
        credential = Credential.objects.create(
            agent=agent,
            name="test-key",
            key_prefix="lgat_abcd",
            key_hash="abc123",
            scopes=["negotiate"],
        )
        assert credential.agent == agent
        assert credential.name == "test-key"
        assert credential.is_active is True

    def test_credential_is_active(self, user: User, agent: Agent) -> None:
        """Credential is active when not revoked and not expired."""
        credential = Credential.objects.create(
            agent=agent,
            name="test-key",
            key_prefix="lgat_abcd",
            key_hash="abc123",
        )
        assert credential.is_active is True

    def test_credential_revoked_is_not_active(self, user: User, agent: Agent) -> None:
        """Revoked credential is not active."""
        credential = Credential.objects.create(
            agent=agent,
            name="test-key",
            key_prefix="lgat_abcd",
            key_hash="abc123",
        )
        credential.revoke()
        assert credential.is_active is False

    def test_credential_expired_is_not_active(self, user: User, agent: Agent) -> None:
        """Expired credential is not active."""
        from datetime import timedelta

        credential = Credential.objects.create(
            agent=agent,
            name="test-key",
            key_prefix="lgat_abcd",
            key_hash="abc123",
            expires_at=timezone.now() - timedelta(days=1),
        )
        assert credential.is_active is False

    def test_cascade_delete_with_agent(self, user: User, agent: Agent) -> None:
        """Deleting agent deletes its credentials."""
        credential = Credential.objects.create(
            agent=agent,
            name="test-key",
            key_prefix="lgat_abcd",
            key_hash="abc123",
        )
        credential_id = credential.id
        agent.delete()
        assert not Credential.objects.filter(id=credential_id).exists()


@pytest.mark.django_db
class TestGenerateAPIKey:
    """Tests for API key generation."""

    def test_generate_api_key(self) -> None:
        """API key generation produces valid format."""
        full_key, key_prefix = generate_api_key()
        assert full_key.startswith("lgat_")
        assert key_prefix.startswith("lgat_")
        assert len(full_key) > 20
        assert key_prefix in full_key

    def test_generate_unique_keys(self) -> None:
        """Each generated key is unique."""
        keys = [generate_api_key() for _ in range(100)]
        full_keys = [k[0] for k in keys]
        assert len(set(full_keys)) == 100  # All unique


@pytest.mark.django_db
class TestHashAPIKey:
    """Tests for API key hashing."""

    def test_hash_is_deterministic(self) -> None:
        """Same key produces same hash."""
        key = "lgat_test_key_123"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2

    def test_different_keys_different_hashes(self) -> None:
        """Different keys produce different hashes."""
        hash1 = hash_api_key("key1")
        hash2 = hash_api_key("key2")
        assert hash1 != hash2

    def test_hash_is_sha256(self) -> None:
        """Hash is a valid SHA-256 hex string."""
        key_hash = hash_api_key("test_key")
        assert len(key_hash) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in key_hash)


@pytest.mark.django_db
class TestCreateCredential:
    """Tests for credential creation service."""

    def test_create_credential(self, user: User, agent: Agent) -> None:
        """Credential can be created via service."""
        credential, full_key = create_credential(
            agent=agent,
            name="test-key",
            scopes=["negotiate", "propose"],
            user=user,
        )
        assert credential.agent == agent
        assert credential.name == "test-key"
        assert credential.scopes == ["negotiate", "propose"]
        assert full_key.startswith("lgat_")
        assert credential.key_hash == hash_api_key(full_key)

    def test_create_credential_for_other_agent_raises(self, user: User, agent: Agent) -> None:
        """Cannot create credential for another user's agent."""
        other_user = User.objects.create_user(email="other@example.com", password="pass")
        other_agent = Agent.objects.create(
            owner=other_user,
            agent_type=AgentType.USER_AGENT,
            name="Other Agent",
        )
        with pytest.raises(ValueError, match="own agents"):
            create_credential(
                agent=other_agent,
                name="test-key",
                user=user,
            )

    def test_create_credential_creates_audit_event(self, user: User, agent: Agent) -> None:
        """Creating credential creates audit event."""
        from apps.audit.models import AuditEvent

        initial_count = AuditEvent.objects.count()
        create_credential(
            agent=agent,
            name="test-key",
            user=user,
        )
        assert AuditEvent.objects.count() == initial_count + 1


@pytest.mark.django_db
class TestRevokeCredential:
    """Tests for credential revocation."""

    def test_revoke_credential(self, user: User, agent: Agent) -> None:
        """Credential can be revoked."""
        credential, _ = create_credential(
            agent=agent,
            name="test-key",
            user=user,
        )
        revoke_credential(credential=credential, user=user)
        credential.refresh_from_db()
        assert credential.revoked_at is not None
        assert credential.is_active is False

    def test_revoke_already_revoked_is_noop(self, user: User, agent: Agent) -> None:
        """Revoking an already revoked credential is a no-op."""
        credential, _ = create_credential(
            agent=agent,
            name="test-key",
            user=user,
        )
        revoke_credential(credential=credential, user=user)
        first_revoked_at = credential.revoked_at

        revoke_credential(credential=credential, user=user)
        credential.refresh_from_db()
        assert credential.revoked_at == first_revoked_at

    def test_revoke_for_other_agent_raises(self, user: User, agent: Agent) -> None:
        """Cannot revoke credential for another user's agent."""
        other_user = User.objects.create_user(email="other@example.com", password="pass")
        other_agent = Agent.objects.create(
            owner=other_user,
            agent_type=AgentType.USER_AGENT,
            name="Other Agent",
        )
        credential, _ = create_credential(
            agent=other_agent,
            name="test-key",
            user=other_user,
        )
        with pytest.raises(ValueError, match="own agents"):
            revoke_credential(credential=credential, user=user)


@pytest.mark.django_db
class TestRotateCredential:
    """Tests for credential rotation."""

    def test_rotate_credential(self, user: User, agent: Agent) -> None:
        """Credential rotation revokes old and creates new."""
        old_credential, old_key = create_credential(
            agent=agent,
            name="old-key",
            scopes=["negotiate"],
            user=user,
        )

        new_credential, new_key = rotate_credential(
            old_credential=old_credential,
            new_name="new-key",
            user=user,
        )

        # Old credential is revoked
        old_credential.refresh_from_db()
        assert old_credential.revoked_at is not None
        assert old_credential.is_active is False

        # New credential is active
        assert new_credential.is_active is True
        assert new_credential.name == "new-key"
        assert new_credential.scopes == ["negotiate"]
        assert new_key != old_key

    def test_rotate_creates_audit_events(self, user: User, agent: Agent) -> None:
        """Rotation creates audit events for both revoke and create."""
        from apps.audit.models import AuditEvent

        old_credential, _ = create_credential(
            agent=agent,
            name="old-key",
            user=user,
        )

        initial_count = AuditEvent.objects.count()
        rotate_credential(
            old_credential=old_credential,
            new_name="new-key",
            user=user,
        )
        # Should create 2 audit events: revoke + create
        assert AuditEvent.objects.count() == initial_count + 2


@pytest.mark.django_db
class TestVerifyAPIKey:
    """Tests for API key verification."""

    def test_verify_valid_key(self, user: User, agent: Agent) -> None:
        """Valid API key returns credential."""
        credential, full_key = create_credential(
            agent=agent,
            name="test-key",
            user=user,
        )
        verified = verify_api_key(full_key)
        assert verified is not None
        assert verified.id == credential.id

    def test_verify_invalid_key_returns_none(self, user: User, agent: Agent) -> None:
        """Invalid API key returns None."""
        verified = verify_api_key("invalid_key")
        assert verified is None

    def test_verify_revoked_key_returns_none(self, user: User, agent: Agent) -> None:
        """Revoked API key returns None."""
        credential, full_key = create_credential(
            agent=agent,
            name="test-key",
            user=user,
        )
        revoke_credential(credential=credential, user=user)
        verified = verify_api_key(full_key)
        assert verified is None

    def test_verify_updates_last_used_at(self, user: User, agent: Agent) -> None:
        """Verification updates last_used_at."""
        credential, full_key = create_credential(
            agent=agent,
            name="test-key",
            user=user,
        )
        assert credential.last_used_at is None

        verify_api_key(full_key)
        credential.refresh_from_db()
        assert credential.last_used_at is not None
