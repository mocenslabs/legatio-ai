import { apiClient } from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { CreateNegotiationPayload, NegotiationRoom, Proposal } from '@/types/domain'

function unwrapList<T>(data: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object' && 'results' in data) return data.results
  return []
}

export async function listNegotiations(): Promise<NegotiationRoom[]> {
  const { data } = await apiClient.get<
    NegotiationRoom[] | PaginatedResponse<NegotiationRoom>
  >('/negotiations/')
  return unwrapList(data)
}

export async function getNegotiation(id: string): Promise<NegotiationRoom> {
  const { data } = await apiClient.get<NegotiationRoom>(`/negotiations/${id}/`)
  return data
}

export async function createNegotiation(
  payload: CreateNegotiationPayload,
): Promise<NegotiationRoom> {
  const { data } = await apiClient.post<NegotiationRoom>('/negotiations/', payload)
  return data
}

export async function startNegotiation(id: string): Promise<NegotiationRoom> {
  const { data } = await apiClient.post<NegotiationRoom>(`/negotiations/${id}/start/`)
  return data
}

export interface ProcessRoundResult {
  room: NegotiationRoom
  round_result: {
    round_number: number
    proposal: Proposal
    outcome: string
    policy_decision?: {
      outcome: string
      risk_level?: string
      reason?: string
    }
    counter_offer?: unknown
  }
}

export async function processRound(id: string): Promise<ProcessRoundResult> {
  const { data } = await apiClient.post<ProcessRoundResult>(
    `/negotiations/${id}/process_round/`,
  )
  return data
}

export async function listProposals(roomId: string): Promise<Proposal[]> {
  const { data } = await apiClient.get<Proposal[] | PaginatedResponse<Proposal>>(
    `/negotiations/${roomId}/proposals/`,
  )
  return unwrapList(data)
}
