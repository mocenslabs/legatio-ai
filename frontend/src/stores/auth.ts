import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authApi from '@/api/auth'
import type { LoginPayload, ProfileUpdatePayload, RegisterPayload, User } from '@/types/auth'
import { extractApiMessage } from '@/utils/errors'
import { tokenStorage } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(tokenStorage.getAccess())
  const bootstrapped = ref(false)
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)
  /** Pending credentials when server requires 2FA */
  const pending2fa = ref<{ email: string; password: string } | null>(null)

  const isAuthenticated = computed(() => Boolean(accessToken.value))

  function setSession(token: string, nextUser?: User | null): void {
    accessToken.value = token
    tokenStorage.setAccess(token)
    if (nextUser) user.value = nextUser
    pending2fa.value = null
  }

  function clearSession(): void {
    accessToken.value = null
    user.value = null
    pending2fa.value = null
    tokenStorage.clear()
  }

  async function bootstrap(): Promise<void> {
    if (!accessToken.value) {
      bootstrapped.value = true
      return
    }
    try {
      user.value = await authApi.fetchCurrentUser()
    } catch {
      /* interceptor may clear on 401 */
    } finally {
      bootstrapped.value = true
    }
  }

  async function login(payload: LoginPayload): Promise<'ok' | 'requires_2fa'> {
    loading.value = true
    errorMessage.value = null
    try {
      const data = await authApi.loginRequest(payload)
      if (data.requires_2fa) {
        pending2fa.value = { email: payload.email, password: payload.password }
        return 'requires_2fa'
      }
      const token = data.access
      if (!token) throw new Error('No access token in response')
      if (data.refresh) tokenStorage.setRefresh(data.refresh)
      setSession(token, data.user ?? null)
      if (!user.value) {
        try {
          user.value = await authApi.fetchCurrentUser()
        } catch {
          user.value = {
            id: '',
            email: payload.email,
            first_name: '',
            last_name: '',
          }
        }
      }
      return 'ok'
    } catch (err) {
      clearSession()
      errorMessage.value = extractApiMessage(err, 'Invalid email or password')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function verify2faLogin(code: string): Promise<void> {
    if (!pending2fa.value) throw new Error('No pending 2FA login')
    loading.value = true
    errorMessage.value = null
    try {
      const data = await authApi.login2faRequest({
        email: pending2fa.value.email,
        password: pending2fa.value.password,
        code,
      })
      const token = data.access
      if (!token) throw new Error('No access token')
      if (data.refresh) tokenStorage.setRefresh(data.refresh)
      setSession(token, data.user ?? null)
      if (!user.value) user.value = await authApi.fetchCurrentUser()
    } catch (err) {
      errorMessage.value = extractApiMessage(err, 'Invalid 2FA code')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload): Promise<void> {
    loading.value = true
    errorMessage.value = null
    try {
      const data = await authApi.registerRequest(payload)
      if ('access' in data && data.access) {
        if (data.refresh) tokenStorage.setRefresh(data.refresh)
        setSession(data.access, data.user ?? null)
      } else {
        await login({ email: payload.email, password: payload.password })
        return
      }
      if (!user.value) {
        try {
          user.value = await authApi.fetchCurrentUser()
        } catch {
          user.value = {
            id: '',
            email: payload.email,
            first_name: payload.first_name ?? '',
            last_name: payload.last_name ?? '',
          }
        }
      }
    } catch (err) {
      errorMessage.value = extractApiMessage(err, 'Registration failed')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refreshProfile(): Promise<void> {
    user.value = await authApi.fetchCurrentUser()
  }

  async function updateProfile(payload: ProfileUpdatePayload): Promise<void> {
    user.value = await authApi.updateProfile(payload)
  }

  function logout(): void {
    clearSession()
  }

  return {
    user,
    accessToken,
    bootstrapped,
    loading,
    errorMessage,
    pending2fa,
    isAuthenticated,
    bootstrap,
    login,
    verify2faLogin,
    register,
    refreshProfile,
    updateProfile,
    logout,
    setSession,
    clearSession,
  }
})
