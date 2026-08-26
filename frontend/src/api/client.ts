/**
 * Axios API client with JWT authentication.
 *
 * Automatically attaches the access token to requests and handles
 * token refresh on 401 responses.
 *
 * Reference: 02-ARCHITECTURE.md Section 9
 */

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor: attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor: handle 401 (token refresh logic for Phase 2)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // TODO: Implement token refresh in Phase 2
      const authStore = useAuthStore()
      authStore.logout()
    }
    return Promise.reject(error)
  },
)
