import { apiClient } from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { Constitution, CreateConstitutionPayload } from '@/types/domain'

export interface PolicyRuleRow {
  id?: string
  rule_number?: number
  name: string
  description?: string
  category?: string
  field?: string
  operator?: string
  value?: unknown
  action?: string
  priority?: number
  version?: string
  is_active?: boolean
}

export interface ConstitutionVersion {
  id: string
  version_number?: number
  status?: string
  created_at?: string
  rules_count?: number
  rules_snapshot?: PolicyRuleRow[]
  rules?: PolicyRuleRow[]
}

export interface RuleInputPayload {
  rule_number: number
  name: string
  description?: string
  category: string
  field: string
  operator: string
  value: unknown
  action: string
  priority?: number
}

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

export async function createConstitutionWithRules(payload: {
  agent_id: string
  name: string
  description?: string
  rules: RuleInputPayload[]
}): Promise<{
  constitution: Constitution
  version?: ConstitutionVersion
  rules_count?: number
}> {
  const { data } = await apiClient.post<{
    constitution: Constitution
    version?: ConstitutionVersion
    rules_count?: number
  }>('/constitutions/with-rules/', payload)
  return data
}

export async function listVersions(constitutionId: string): Promise<ConstitutionVersion[]> {
  const { data } = await apiClient.get<
    ConstitutionVersion[] | PaginatedResponse<ConstitutionVersion>
  >(`/constitutions/${constitutionId}/versions/`)
  return unwrapList(data)
}

export async function activateConstitution(
  constitutionId: string,
  versionId: string,
  options?: { replaceActive?: boolean },
): Promise<{ constitution: Constitution }> {
  const { data } = await apiClient.post<{ constitution: Constitution }>(
    `/constitutions/${constitutionId}/activate/`,
    {
      version_id: versionId,
      replace_active: Boolean(options?.replaceActive),
    },
  )
  return data
}

/** True when backend rejected activate because another constitution is ACTIVE. */
export function isActiveConflictError(err: unknown): boolean {
  const e = err as {
    response?: { data?: { error?: string; code?: string; detail?: string } }
    message?: string
  }
  const data = e?.response?.data
  const blob = `${data?.error || ''} ${data?.code || ''} ${data?.detail || ''} ${e?.message || ''}`
  return /already has an active constitution|MultipleActiveConstitutions/i.test(blob)
}
