import { apiClient } from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { Agent } from '@/types/domain'

function unwrapList<T>(data: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object' && 'results' in data) return data.results
  return []
}

export async function listAgents(): Promise<Agent[]> {
  const { data } = await apiClient.get<Agent[] | PaginatedResponse<Agent>>('/agents/')
  return unwrapList(data)
}

export async function getAgent(id: string): Promise<Agent> {
  const { data } = await apiClient.get<Agent>(`/agents/${id}/`)
  return data
}

export interface CreateAgentPayload {
  name: string
  description?: string
  capabilities?: string[]
}

export async function createAgent(payload: CreateAgentPayload): Promise<Agent> {
  const { data } = await apiClient.post<Agent>('/agents/', payload)
  return data
}

export async function deleteAgent(id: string): Promise<void> {
  await apiClient.delete(`/agents/${id}/`)
}
