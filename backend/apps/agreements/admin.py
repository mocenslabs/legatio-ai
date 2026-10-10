"""Django Admin for agreements app."""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.agreements.models import Agreement, AgreementSignature


class AgreementSignatureInline(admin.StackedInline):  # type: ignore[type-arg]
    model = AgreementSignature
    extra = 0
    readonly_fields = (
        "id",
        "signer",
        "signature_algorithm",
        "signature_value",
        "signed_payload_hash",
        "ip_address",
        "user_agent_string",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "reference_code",
        "room",
        "status",
        "signer_email",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("reference_code", "room__reference_code")
    readonly_fields = (
        "id",
        "reference_code",
        "room",
        "proposal",
        "constitution_version",
        "status",
        "canonical_json",
        "canonical_hash",
        "parties",
        "terms_summary",
        "signed_at",
        "executed_at",
        "voided_at",
        "created_at",
    )
    inlines = [AgreementSignatureInline]

    def signer_email(self, obj: Agreement) -> str:
        if hasattr(obj, "signature") and obj.signature:
            return obj.signature.signer.email
        return "Not signed"

    signer_email.short_description = "Signer"  # type: ignore[attr-defined]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False  # Created via service layer only

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False  # Immutable

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False  # Immutable


@admin.register(AgreementSignature)
class AgreementSignatureAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "agreement", "signer", "signature_algorithm", "created_at")
    readonly_fields = (
        "id",
        "agreement",
        "signer",
        "signature_algorithm",
        "signature_value",
        "signed_payload_hash",
        "ip_address",
        "user_agent_string",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
