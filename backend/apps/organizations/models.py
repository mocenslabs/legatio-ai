"""
Organization and membership models for multi-tenant Legatio.

Personal agents remain owned by User. Organization is optional scope
for company workspaces (agents, constitutions, future billing).
"""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.organizations.managers import SoftDeleteManager
from core.enums import OrganizationRole, OrganizationStatus


class Organization(models.Model):
    """Company / workspace container."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organizations_created",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # noqa: DJ012

    class Meta:
        db_table = "legatio_organizations_organization"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="idx_org_slug"),
            models.Index(fields=["status"], name="idx_org_status"),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            base = slugify(self.name)[:200] or "org"
            candidate = base
            n = 1
            while Organization.all_objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                n += 1
                candidate = f"{base}-{n}"
            self.slug = candidate
        super().save(*args, **kwargs)

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.status = OrganizationStatus.ARCHIVED
        self.save(update_fields=["deleted_at", "status", "updated_at"])


class OrganizationMembership(models.Model):
    """User membership in an organization with a role."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=OrganizationRole.choices,
        default=OrganizationRole.MEMBER,
        db_index=True,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_invites_sent",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legatio_organizations_membership"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="uniq_org_user_membership",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "role"], name="idx_membership_user_role"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.organization_id} ({self.role})"

    @property
    def is_owner(self) -> bool:
        return self.role == OrganizationRole.OWNER

    @property
    def can_manage_members(self) -> bool:
        return self.role in (OrganizationRole.OWNER, OrganizationRole.ADMIN)
