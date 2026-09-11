<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth'
import LegatioLogo from '@/components/LegatioLogo.vue'
import LegatioThemeToggle from '@/components/LegatioThemeToggle.vue'

const route = useRoute()
const authStore = useAuthStore()

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/constitutions', label: 'Constitutions' },
  { to: '/negotiations', label: 'Negotiations' },
  { to: '/approvals', label: 'Approvals' },
  { to: '/audit', label: 'Audit' },
]

function isActive(path: string): boolean {
  return route.path === path
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background">
    <!-- Top navigation bar -->
    <header class="sticky top-0 z-50 w-full border-b border-border bg-card/80 backdrop-blur-sm">
      <div class="container mx-auto flex items-center justify-between h-16 px-4">
        <!-- Logo -->
        <RouterLink to="/" class="flex items-center gap-2">
          <LegatioLogo />
        </RouterLink>

        <!-- Nav Links (Solo si está autenticado) -->
        <nav v-if="authStore.isAuthenticated" class="hidden md:flex gap-1">
          <Button
            v-for="item in navItems"
            :key="item.to"
            :variant="isActive(item.to) ? 'default' : 'ghost'"
            size="sm"
            as-child
          >
            <RouterLink :to="item.to">{{ item.label }}</RouterLink>
          </Button>
        </nav>

        <!-- Right Actions -->
        <div class="flex items-center gap-2">
          <LegatioThemeToggle />

          <template v-if="authStore.isAuthenticated">
            <span class="hidden sm:inline-block text-sm text-muted-foreground mr-2">
              {{ authStore.fullName }}
            </span>
            <Button variant="outline" size="sm" @click="authStore.logout()">
              {{ $t('common.actions.signOut') }}
            </Button>
          </template>
          <template v-else>
            <Button variant="ghost" size="sm" as-child>
              <RouterLink to="/login">{{ $t('common.actions.signIn') }}</RouterLink>
            </Button>
            <Button size="sm" as-child>
              <RouterLink to="/register">{{ $t('common.actions.getStarted') }}</RouterLink>
            </Button>
          </template>
        </div>
      </div>
    </header>

    <!-- Page content -->
    <main class="flex-1 container mx-auto px-4 py-8">
      <RouterView />
    </main>
  </div>
</template>
