import type { AxiosError } from 'axios'

import type { ApiErrorBody } from '@/types/api'

function formatDetails(details: unknown): string | null {
  if (!details || typeof details !== 'object') return null
  const parts: string[] = []
  for (const [key, value] of Object.entries(details as Record<string, unknown>)) {
    if (Array.isArray(value)) {
      parts.push(`${key}: ${value.map(String).join(', ')}`)
    } else if (value != null && value !== '') {
      parts.push(`${key}: ${String(value)}`)
    }
  }
  return parts.length ? parts.join(' · ') : null
}

/**
 * Extract a human-readable message from an API / Axios error.
 * Pass an i18n string as fallback (e.g. t('errors.unknown') or t('errors.network')).
 */
export function extractApiMessage(
  error: unknown,
  fallback = 'Unexpected error',
): string {
  if (!error || typeof error !== 'object') return fallback

  const axiosError = error as AxiosError<ApiErrorBody>
  const data = axiosError.response?.data

  if (!axiosError.response) {
    // Network / CORS / offline
    return fallback
  }

  if (data?.error?.message) {
    const details = formatDetails(
      (data.error as { details?: unknown }).details,
    )
    return details ? `${data.error.message} (${details})` : data.error.message
  }
  if (typeof data?.detail === 'string') return data.detail
  if (typeof data?.message === 'string') return data.message

  const status = axiosError.response.status
  if (status === 401) return fallback
  if (status === 403) return fallback
  if (status >= 500) return fallback

  return fallback
}

export function isUnauthorized(error: unknown): boolean {
  const axiosError = error as AxiosError
  return axiosError.response?.status === 401
}
