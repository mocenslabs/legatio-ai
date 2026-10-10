/** Date + status helpers. Labels go through i18n in the view via statusLabelKey(). */

export function formatDate(value?: string | null): string {
  if (!value) return '—'
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

export function statusBadgeClass(status?: string): string {
  const s = (status || '').toUpperCase()
  if (
    ['ACTIVE', 'APPROVED', 'SIGNED', 'COMPLETED', 'ACCEPTED', 'ALLOWED', 'EXECUTED'].includes(s)
  ) {
    return 'badge badge--success'
  }
  if (
    [
      'PENDING',
      'PENDING_APPROVAL',
      'AWAITING_APPROVAL',
      'IN_PROGRESS',
      'DRAFT',
      'REQUIRE_HUMAN_APPROVAL',
    ].includes(s)
  ) {
    return 'badge badge--warning'
  }
  if (['REJECTED', 'DENIED', 'FAILED', 'CANCELLED', 'EXPIRED', 'REVOKED', 'SUSPENDED'].includes(s)) {
    return 'badge badge--danger'
  }
  return 'badge badge--neutral'
}

/** i18n key under status.* — falls back to raw status if unknown */
export function statusLabelKey(status?: string): string {
  if (!status) return 'status.unknown'
  const s = status.toUpperCase().replace(/-/g, '_')
  const map: Record<string, string> = {
    ACTIVE: 'status.active',
    DRAFT: 'status.draft',
    PENDING: 'status.pending',
    IN_PROGRESS: 'status.inProgress',
    AWAITING_APPROVAL: 'status.awaitingApproval',
    PENDING_APPROVAL: 'status.awaitingApproval',
    REQUIRE_HUMAN_APPROVAL: 'status.awaitingApproval',
    APPROVED: 'status.approved',
    REJECTED: 'status.rejected',
    DENIED: 'status.denied',
    ALLOWED: 'status.allowed',
    COMPLETED: 'status.completed',
    SIGNED: 'status.signed',
    EXECUTED: 'status.executed',
    CANCELLED: 'status.cancelled',
    EXPIRED: 'status.expired',
    SUSPENDED: 'status.suspended',
    REVOKED: 'status.revoked',
    FAILED: 'status.failed',
    ARCHIVED: 'status.archived',
  }
  return map[s] || 'status.raw'
}
