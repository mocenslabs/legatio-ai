/**
 * Replace frontend/src/router/guards.ts
 * Home and public help are accessible without auth.
 */
import type { Router } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

export function setupRouterGuards(router: Router): void {
  router.beforeEach(async (to) => {
    const auth = useAuthStore()

    if (!auth.bootstrapped) {
      await auth.bootstrap()
    }

    const isPublic = to.matched.some((r) => r.meta.public === true)
    const requiresAuth = to.matched.some((r) => r.meta.requiresAuth === true)
    const guestOnly = to.matched.some((r) => r.meta.guestOnly === true)

    if (requiresAuth && !auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    if (guestOnly && auth.isAuthenticated) {
      return { name: 'dashboard' }
    }

    // Public routes always allowed (home, public help)
    if (isPublic) {
      return true
    }

    return true
  })
}
