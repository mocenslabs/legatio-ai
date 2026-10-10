import { apiClient } from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { Constitution, CreateConstitutionPayload } from '@/types/domain'

function unwrapList<T>(data: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object' && 'results' in data) return data.results
  return []
}

export async function listConstitutions(): Promise<Constitution[]> {
  const { data } = await apiClient.get<Constitution[] | PaginatedResponse<Constitution>>(
    '/constitutions/',
  )
  return unwrapList(data)
}

export async function getConstitution(id: string): Promise<Constitution> {
  const { data } = await apiClient.get<Constitution>(`/constitutions/${id}/`)
  return data
}

export async function createConstitution(
  payload: CreateConstitutionPayload,
): Promise<Constitution> {
  const { data } = await apiClient.post<Constitution>('/constitutions/', payload)
  return data
}
