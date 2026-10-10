"""
Custom managers for the agreements app.
Enforces immutability for Agreement and AgreementSignature records.
Source: 03-DATA-MODEL.md Section 17.2
"""

from typing import Any

from django.db import models


class ImmutableAgreementQuerySet(models.QuerySet["Agreement"]):  # type: ignore[name-defined]
    """QuerySet that prevents updates to signed agreements."""

    def update(self, **kwargs: Any) -> int:
        """Prevent bulk updates on signed agreements."""
        if self.filter(status__in=["SIGNED", "EXECUTED", "VOIDED"]).exists():
            raise RuntimeError("Cannot update signed or executed agreements.")
        return super().update(**kwargs)


class ImmutableAgreementManager(models.Manager["Agreement"]):  # type: ignore[name-defined]
    """Manager that enforces immutability for agreements."""

    def get_queryset(self) -> ImmutableAgreementQuerySet:
        return ImmutableAgreementQuerySet(self.model, using=self._db)


class AppendOnlySignatureQuerySet(models.QuerySet["AgreementSignature"]):  # type: ignore[name-defined]
    """QuerySet that prevents updates and deletes on signatures."""

    def update(self, **kwargs: Any) -> int:
        raise RuntimeError("AgreementSignature records are append-only. UPDATE not allowed.")

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise RuntimeError("AgreementSignature records are append-only. DELETE not allowed.")


class AppendOnlySignatureManager(models.Manager["AgreementSignature"]):  # type: ignore[name-defined]
    """Manager that enforces append-only behavior for signatures."""

    def get_queryset(self) -> AppendOnlySignatureQuerySet:
        return AppendOnlySignatureQuerySet(self.model, using=self._db)
