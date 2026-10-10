"""
Models for the agreements app.
Defines Agreement (immutable record of agreed terms) and AgreementSignature
(cryptographic proof of user consent).
Source: 03-DATA-MODEL.md Section 12
"""

import uuid
from typing import Any

from django.conf import settings
from django.db import models

from apps.agreements.managers import (
    AppendOnlySignatureManager,
    ImmutableAgreementManager,
)
from core.enums import AgreementStatus


class Agreement(models.Model):
    """
    Immutable record of an agreement reached between agents.
    Once signed, this record cannot be modified. The canonical_json
    represents the exact terms that were hashed and signed.
    Source: 03-DATA-MODEL.md Section 12.1
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    reference_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="E.g., AGR-2026-000184",
    )
    room = models.OneToOneField(
        "negotiations.NegotiationRoom",
        on_delete=models.PROTECT,
        related_name="agreement",
        help_text="One agreement per room. PROTECT to preserve history.",
    )
    proposal = models.ForeignKey(
        "proposals.Proposal",
        on_delete=models.PROTECT,
        related_name="agreements",
        help_text="The accepted proposal. PROTECT to preserve history.",
    )
    constitution_version = models.ForeignKey(
        "constitutions.ConstitutionVersion",
        on_delete=models.PROTECT,
        related_name="agreements",
        help_text="Version active at signing time. PROTECT to preserve history.",
    )
    status = models.CharField(
        max_length=20,
        choices=AgreementStatus.choices,
        default=AgreementStatus.DRAFT,
        db_index=True,
    )
    canonical_json = models.JSONField(
        help_text="The exact signed representation (sorted keys, no extra whitespace).",
    )
    canonical_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="SHA-256 of canonical_json.",
    )
    parties = models.JSONField(
        help_text="Agent IDs and roles, e.g., [{'id': 'uuid', 'role': 'buyer'}].",
    )
    terms_summary = models.TextField(
        help_text="Human-readable summary of the terms.",
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user cryptographically signed.",
    )
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user confirmed real-world execution.",
    )
    voided_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the agreement was revoked/voided.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    # Manager
    objects = ImmutableAgreementManager()

    class Meta:
        db_table = "legatio_agreements_agreement"
        verbose_name = "agreement"
        verbose_name_plural = "agreements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["canonical_hash"], name="idx_agreement_hash"),
            models.Index(fields=["status"], name="idx_agreement_status"),
            models.Index(fields=["room"], name="idx_agreement_room"),
        ]

    def __str__(self) -> str:
        return f"Agreement {self.reference_code} ({self.get_status_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save to enforce immutability once signed.
        """
        if self.pk:
            existing = Agreement.objects.filter(pk=self.pk).first()
            if existing and existing.status in [
                AgreementStatus.SIGNED,
                AgreementStatus.EXECUTED,
                AgreementStatus.VOIDED,
            ]:
                raise RuntimeError(
                    f"Agreement {self.reference_code} is {existing.status} and cannot be modified."
                )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """Prevent deletion of agreements."""
        raise RuntimeError("Agreement records cannot be deleted.")


class AgreementSignature(models.Model):
    """
    Cryptographic proof of user consent for an agreement.
    Append-only. Once created, it cannot be modified or deleted.
    Source: 03-DATA-MODEL.md Section 12.2
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    agreement = models.OneToOneField(
        Agreement,
        on_delete=models.CASCADE,
        related_name="signature",
        help_text="The agreement this signature applies to.",
    )
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="signatures",
        help_text="The user who signed. PROTECT to preserve audit history.",
    )
    signature_algorithm = models.CharField(
        max_length=20,
        help_text="E.g., 'HMAC-SHA256' (MVP).",
    )
    signature_value = models.CharField(
        max_length=128,
        help_text="The cryptographic signature value.",
    )
    signed_payload_hash = models.CharField(
        max_length=64,
        help_text="Must exactly match agreement.canonical_hash.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the signer.",
    )
    user_agent_string = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Browser/client user agent.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    # Manager
    objects = AppendOnlySignatureManager()

    class Meta:
        db_table = "legatio_agreements_agreementsignature"
        verbose_name = "agreement signature"
        verbose_name_plural = "agreement signatures"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Signature for {self.agreement.reference_code} by {self.signer.email}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save to enforce append-only behavior and hash match invariant.
        """
        if self.pk and not self._state.adding:
            raise RuntimeError("AgreementSignature records are append-only. Cannot update.")
        # Invariant: signed_payload_hash MUST equal agreement.canonical_hash
        if self.signed_payload_hash != self.agreement.canonical_hash:
            raise ValueError("signed_payload_hash must exactly match agreement.canonical_hash")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """Prevent deletion of signatures."""
        raise RuntimeError("AgreementSignature records are append-only. Cannot delete.")
