import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

interface QueuedRequest {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

type RetryableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean }

let isRefreshing = false
let failedQueue: QueuedRequest[] = []

function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach((queued) => {
    if (error) {
      queued.reject(error)
    } else if (token) {
      queued.resolve(token)
    }
  })
  failedQueue = []
}

apiClient.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || !error.config || error.response?.status !== 401) {
      return Promise.reject(error)
    }

    const originalRequest = error.config as RetryableRequestConfig
    if (originalRequest._retry) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
        .catch((queueError: unknown) => Promise.reject(queueError))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const authStore = useAuthStore()
      const { data } = await axios.post<{ access: string; refresh: string }>(
        `${API_BASE_URL}/auth/refresh/`,
        { refresh: authStore.refreshToken },
      )
      authStore.setTokens(data.access, data.refresh)
      processQueue(null, data.access)
      originalRequest.headers.Authorization = `Bearer ${data.access}`
      return apiClient(originalRequest)
    } catch (refreshError: unknown) {
      processQueue(refreshError, null)
      useAuthStore().logout()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)
