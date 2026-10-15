/** Display helpers — prefer human labels via i18n keys (status.*). */

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

export function formatMoney(amount?: number | string | null, currency = 'EUR'): string {
  if (amount === null || amount === undefined || amount === '') return '—'
  const n = typeof amount === 'string' ? Number(amount) : amount
  if (Number.isNaN(n)) return String(amount)
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(n)
  } catch {
    return `${n} ${currency}`
  }
}

export function statusBadgeClass(status?: string): string {
  if (!status) return 'badge badge--neutral'
  const s = status.toUpperCase().replace(/-/g, '_')
  if (['ACTIVE', 'APPROVED', 'ALLOWED', 'COMPLETED', 'SIGNED', 'EXECUTED'].includes(s)) {
    return 'badge badge--success'
  }
  if (
    [
      'DRAFT',
      'PENDING',
      'IN_PROGRESS',
      'AWAITING_APPROVAL',
      'PENDING_APPROVAL',
      'REQUIRE_APPROVAL',
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

/** i18n key under status.* */
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
    REQUIRE_APPROVAL: 'status.needsYourOk',
    REQUIRE_HUMAN_APPROVAL: 'status.needsYourOk',
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
    USER_AGENT: 'status.yourAgent',
    EXTERNAL_AGENT: 'status.externalAgent',
    SIMULATED: 'status.simulatedAgent',
  }
  return map[s] || 'status.raw'
}

export function agentTypeLabelKey(type?: string): string {
  if (!type) return 'status.raw'
  const s = type.toUpperCase()
  if (s.includes('USER')) return 'status.yourAgent'
  if (s.includes('SIMULATED')) return 'status.simulatedAgent'
  if (s.includes('EXTERNAL')) return 'status.externalAgent'
  return 'status.raw'
}
