/**
 * Authentication store.
 *
 * Manages user authentication state, JWT tokens, and user profile.
 * Will be fully implemented in Phase 2.
 *
 * Reference: 02-ARCHITECTURE.md Section 11.1
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_verified: boolean
  two_factor_enabled: boolean
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value && !!accessToken.value)
  const fullName = computed(() => {
    if (!user.value) return ''
    return `${user.value.first_name} ${user.value.last_name}`.trim()
  })

  // Actions
  function setUser(newUser: User | null): void {
    user.value = newUser
  }

  function setTokens(access: string | null, refresh: string | null): void {
    accessToken.value = access
    refreshToken.value = refresh
  }

  function logout(): void {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
  }

  return {
    // State
    user,
    accessToken,
    refreshToken,
    // Getters
    isAuthenticated,
    fullName,
    // Actions
    setUser,
    setTokens,
    logout,
  }
})
