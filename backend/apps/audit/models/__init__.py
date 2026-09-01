"""Audit models.

This module exports all models from the audit app.
"""

from apps.audit.models.audit_log import AuditAction, AuditLog

__all__ = ["AuditAction", "AuditLog"]
