"""
Services for credential management.

Handles API key generation, hashing, rotation, and revocation.

Source: 03-DATA-MODEL.md Section 7.2
"""

import hashlib
import secrets
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.agents.models import Agent, Credential
from apps.audit.services import create_audit_event
from core.enums import ActorType, EventType


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key with prefix.

    Returns:
        Tuple of (full_key, key_prefix).
        The full key is shown once to the user and never stored.
        The prefix is stored for identification.
    """
    # Generate random 32-byte key
    random_part = secrets.token_urlsafe(32)

    # Generate prefix (first 4 chars of hash for identification)
    prefix_hash = hashlib.sha256(random_part.encode()).hexdigest()[:4]
    key_prefix = f"lgat_{prefix_hash}"

    # Full key format: lgat_<prefix>_<random_part>
    full_key = f"{key_prefix}_{random_part}"

    return full_key, key_prefix


def hash_api_key(full_key: str) -> str:
    """
    Compute SHA-256 hash of the full API key.

    Args:
        full_key: The complete API key.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    return hashlib.sha256(full_key.encode("utf-8")).hexdigest()


def create_credential(
    *,
    agent: Agent,
    name: str,
    scopes: list[str] | None = None,
    expires_at: Any = None,
    user: Any,
) -> tuple[Credential, str]:
    """
    Create a new credential for an agent.

    Args:
        agent: The agent that will own this credential.
        name: Human-readable name for the credential.
        scopes: List of permitted scopes (optional).
        expires_at: Expiration timestamp (optional).
        user: The user creating the credential (for audit).

    Returns:
        Tuple of (credential, full_key).
        The full_key is shown once and must be stored securely by the user.

    Raises:
        ValueError: If agent is not owned by the user.
    """
    # Verify ownership
    if agent.owner != user:
        raise ValueError("You can only create credentials for your own agents.")

    # Generate key
    full_key, key_prefix = generate_api_key()
    key_hash = hash_api_key(full_key)

    # Create credential
    credential = Credential.objects.create(
        agent=agent,
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=scopes or [],
        expires_at=expires_at,
    )

    # Audit event
    create_audit_event(
        event_type=EventType.AGENT_CREDENTIAL_ROTATED,  # Using rotated for creation too
        actor_type=ActorType.USER,
        actor_id=user.id,
        entity_type="Credential",
        entity_id=credential.id,
        payload={
            "agent_id": str(agent.id),
            "name": name,
            "key_prefix": key_prefix,
            "action": "created",
        },
    )

    return credential, full_key


def revoke_credential(
    *,
    credential: Credential,
    user: Any,
) -> None:
    """
    Revoke a credential.

    Args:
        credential: The credential to revoke.
        user: The user revoking the credential (for audit).

    Raises:
        ValueError: If credential is not owned by the user's agent.
    """
    # Verify ownership
    if credential.agent.owner != user:
        raise ValueError("You can only revoke credentials for your own agents.")

    if credential.revoked_at is not None:
        return  # Already revoked

    credential.revoke()

    # Audit event
    create_audit_event(
        event_type=EventType.AGENT_CREDENTIAL_ROTATED,
        actor_type=ActorType.USER,
        actor_id=user.id,
        entity_type="Credential",
        entity_id=credential.id,
        payload={
            "agent_id": str(credential.agent.id),
            "name": credential.name,
            "key_prefix": credential.key_prefix,
            "action": "revoked",
        },
    )


def rotate_credential(
    *,
    old_credential: Credential,
    new_name: str,
    scopes: list[str] | None = None,
    user: Any,
) -> tuple[Credential, str]:
    """
    Rotate a credential: revoke old and create new.

    This is an atomic operation.

    Args:
        old_credential: The credential to replace.
        new_name: Name for the new credential.
        scopes: Scopes for the new credential (optional).
        user: The user performing the rotation (for audit).

    Returns:
        Tuple of (new_credential, full_key).

    Raises:
        ValueError: If credential is not owned by the user's agent.
    """
    # Verify ownership
    if old_credential.agent.owner != user:
        raise ValueError("You can only rotate credentials for your own agents.")

    with transaction.atomic():
        # Revoke old credential
        revoke_credential(credential=old_credential, user=user)

        # Create new credential
        new_credential, full_key = create_credential(
            agent=old_credential.agent,
            name=new_name,
            scopes=scopes or old_credential.scopes,
            user=user,
        )

    return new_credential, full_key


def verify_api_key(full_key: str) -> Credential | None:
    """
    Verify an API key and return the associated credential if valid.

    Args:
        full_key: The complete API key to verify.

    Returns:
        The Credential if valid, None otherwise.
    """
    key_hash = hash_api_key(full_key)

    try:
        credential = Credential.objects.select_related("agent").get(key_hash=key_hash)
    except Credential.DoesNotExist:
        return None

    # Check if active
    if not credential.is_active:
        return None

    # Update last_used_at
    credential.last_used_at = timezone.now()
    credential.save(update_fields=["last_used_at"])

    return credential
