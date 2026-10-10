import { apiClient } from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { Agreement } from '@/types/domain'

function unwrapList<T>(data: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object' && 'results' in data) return data.results
  return []
}

export async function listAgreements(): Promise<Agreement[]> {
  const { data } = await apiClient.get<Agreement[] | PaginatedResponse<Agreement>>('/agreements/')
  return unwrapList(data)
}

export async function getAgreement(id: string): Promise<Agreement> {
  const { data } = await apiClient.get<Agreement>(`/agreements/${id}/`)
  return data
}

export async function signAgreement(id: string): Promise<Agreement | { signature?: unknown }> {
  const { data } = await apiClient.post(`/agreements/${id}/sign/`, {})
  return data
}

export async function getCanonical(id: string): Promise<Record<string, unknown>> {
  const { data } = await apiClient.get<Record<string, unknown>>(`/agreements/${id}/canonical/`)
  return data
}

export async function getSignature(id: string): Promise<Record<string, unknown>> {
  const { data } = await apiClient.get<Record<string, unknown>>(`/agreements/${id}/signature/`)
  return data
}

export async function exportAgreement(id: string): Promise<Blob> {
  const { data } = await apiClient.post(
    `/agreements/${id}/export/`,
    { format: 'json' },
    { responseType: 'blob' },
  )
  return data as Blob
}

export async function verifyAgreement(id: string): Promise<Record<string, unknown>> {
  const { data } = await apiClient.post<Record<string, unknown>>(`/agreements/${id}/verify/`)
  return data
}
