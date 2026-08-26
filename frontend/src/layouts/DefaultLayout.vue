<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth'

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
  <div class="min-h-screen bg-background">
    <!-- Top navigation bar -->
    <header class="border-b border-border bg-card">
      <div class="container mx-auto flex items-center justify-between h-14 px-4">
        <RouterLink to="/" class="font-bold text-lg"> Legatio AI </RouterLink>

        <nav v-if="authStore.isAuthenticated" class="flex gap-1">
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

        <div class="flex items-center gap-2">
          <template v-if="authStore.isAuthenticated">
            <span class="text-sm text-muted-foreground">
              {{ authStore.fullName }}
            </span>
            <Button variant="outline" size="sm" @click="authStore.logout()"> Sign Out </Button>
          </template>
          <template v-else>
            <Button variant="ghost" size="sm" as-child>
              <RouterLink to="/login">Sign In</RouterLink>
            </Button>
            <Button size="sm" as-child>
              <RouterLink to="/register">Get Started</RouterLink>
            </Button>
          </template>
        </div>
      </div>
    </header>

    <!-- Page content -->
    <main>
      <RouterView />
    </main>
  </div>
</template>
