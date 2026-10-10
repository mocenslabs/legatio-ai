import type { AxiosError } from 'axios'

import type { ApiErrorBody } from '@/types/api'

export function extractApiMessage(
  error: unknown,
  fallback = 'Unexpected error',
): string {
  if (!error || typeof error !== 'object') return fallback

  const axiosError = error as AxiosError<ApiErrorBody>
  const data = axiosError.response?.data

  if (data?.error?.message) return data.error.message
  if (typeof data?.detail === 'string') return data.detail
  if (typeof data?.message === 'string') return data.message

  if (axiosError.message === 'Network Error') return 'Network error'

  return fallback
}

export function isUnauthorized(error: unknown): boolean {
  const axiosError = error as AxiosError
  return axiosError.response?.status === 401
}
