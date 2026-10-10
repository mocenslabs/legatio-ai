export interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
  detail?: string
  message?: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
