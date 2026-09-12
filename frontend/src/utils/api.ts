import { isAxiosError } from 'axios'
import type { PaginatedResponse } from '@/types/api/constitutions'

/** Normalize DRF responses that may be paginated or plain arrays. */
export function unwrapPaginated<T>(data: PaginatedResponse<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results
}

/** HTTP status of an unknown error, when it originates from Axios. */
export function getErrorStatus(error: unknown): number | undefined {
  return isAxiosError(error) ? error.response?.status : undefined
}

/** Human-readable message from DRF error payloads (`detail` or ADR error envelope). */
export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!isAxiosError(error)) return fallback

  const data = error.response?.data as { detail?: string; error?: { message?: string } } | undefined

  if (typeof data?.detail === 'string') return data.detail
  if (typeof data?.error?.message === 'string') return data.error.message
  return fallback
}
