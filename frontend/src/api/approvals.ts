import { apiClient } from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { ApprovalRequest } from '@/types/domain'

function unwrapList<T>(data: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object' && 'results' in data) return data.results
  return []
}

export async function listPendingApprovals(): Promise<ApprovalRequest[]> {
  const { data } = await apiClient.get<
    ApprovalRequest[] | PaginatedResponse<ApprovalRequest>
  >('/approvals/pending/')
  return unwrapList(data)
}

export async function listApprovals(): Promise<ApprovalRequest[]> {
  const { data } = await apiClient.get<
    ApprovalRequest[] | PaginatedResponse<ApprovalRequest>
  >('/approvals/')
  return unwrapList(data)
}

export async function approveRequest(
  id: string,
  comment = '',
): Promise<unknown> {
  const { data } = await apiClient.post(`/approvals/${id}/approve/`, { comment })
  return data
}

export async function rejectRequest(
  id: string,
  comment = '',
): Promise<unknown> {
  const { data } = await apiClient.post(`/approvals/${id}/reject/`, { comment })
  return data
}
