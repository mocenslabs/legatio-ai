import { apiClient } from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { AuditEvent } from '@/types/domain'

function unwrapList<T>(data: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object' && 'results' in data) return data.results
  return []
}

export async function listAuditEvents(): Promise<AuditEvent[]> {
  const { data } = await apiClient.get<AuditEvent[] | PaginatedResponse<AuditEvent>>(
    '/audit/events/',
  )
  return unwrapList(data)
}

export async function getEntityAuditTrail(
  entityType: string,
  entityId: string,
): Promise<AuditEvent[]> {
  const { data } = await apiClient.get<AuditEvent[] | PaginatedResponse<AuditEvent>>(
    `/audit/entities/${entityType}/${entityId}/`,
  )
  return unwrapList(data)
}

export async function verifyAuditChain(): Promise<Record<string, unknown>> {
  const { data } = await apiClient.post<Record<string, unknown>>('/audit/verify/')
  return data
}
