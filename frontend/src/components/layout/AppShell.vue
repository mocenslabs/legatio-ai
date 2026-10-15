<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import * as approvalsApi from '@/api/approvals'
import LocaleSwitch from '@/components/common/LocaleSwitch.vue'
import ThemeSwitch from '@/components/common/ThemeSwitch.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const sidebarOpen = ref(false)
const pendingApprovals = ref(0)

const displayName = computed(() => {
  const u = auth.user
  if (!u) return ''
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
  return name || u.email || ''
})

const navItems = computed(() => [
  { name: 'dashboard', label: t('nav.dashboard'), to: { name: 'dashboard' }, badge: 0 },
  { name: 'agents', label: t('nav.agents'), to: { name: 'agents' }, badge: 0 },
  { name: 'constitutions', label: t('nav.constitutions'), to: { name: 'constitutions' }, badge: 0 },
  { name: 'negotiations', label: t('nav.negotiations'), to: { name: 'negotiations' }, badge: 0 },
  {
    name: 'approvals',
    label: t('nav.approvals'),
    to: { name: 'approvals' },
    badge: pendingApprovals.value,
  },
  { name: 'agreements', label: t('nav.agreements'), to: { name: 'agreements' }, badge: 0 },
  { name: 'audit', label: t('nav.audit'), to: { name: 'audit' }, badge: 0 },
  { name: 'help', label: t('nav.help'), to: { name: 'help' }, badge: 0 },
])

const pageTitle = computed(() => {
  const key = route.meta.titleKey as string | undefined
  if (key) return t(key)
  return t('app.name')
})

async function refreshPending(): Promise<void> {
  if (!auth.isAuthenticated) {
    pendingApprovals.value = 0
    return
  }
  try {
    const list = await approvalsApi.listPendingApprovals()
    pendingApprovals.value = list.length
  } catch {
    pendingApprovals.value = 0
  }
}

watch(
  () => route.fullPath,
  () => {
    sidebarOpen.value = false
    void refreshPending()
  },
)

onMounted(() => {
  void refreshPending()
})

function toggleSidebar(): void {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar(): void {
  sidebarOpen.value = false
}

function onLogout(): void {
  auth.logout()
  void router.push({ name: 'login' })
}
</script>

<template>
  <div
    class="app-shell"
    :class="{ 'is-sidebar-open': sidebarOpen }"
  >
    <div
      class="app-shell__backdrop"
      @click="closeSidebar"
    />

    <aside class="app-shell__sidebar">
      <div class="app-shell__brand">
        {{ t('app.name') }}
      </div>
      <nav
        class="app-shell__nav"
        :aria-label="t('app.name')"
      >
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.to"
          class="app-shell__nav-link"
          active-class="is-active"
        >
          <span>{{ item.label }}</span>
          <span
            v-if="item.badge > 0"
            class="nav-badge"
            :aria-label="String(item.badge)"
          >
            {{ item.badge > 9 ? '9+' : item.badge }}
          </span>
        </router-link>
      </nav>
    </aside>

    <header class="app-shell__header">
      <div class="app-shell__header-left">
        <button
          type="button"
          class="app-shell__menu-btn"
          :aria-label="t('common.menu')"
          :aria-expanded="sidebarOpen"
          @click="toggleSidebar"
        >
          ☰
        </button>
        <div class="app-shell__page-title">
          {{ pageTitle }}
        </div>
      </div>
      <div class="app-shell__header-right">
        <ThemeSwitch />
        <LocaleSwitch />
        <RouterLink
          v-if="auth.user"
          :to="{ name: 'profile' }"
          class="app-shell__user-chip"
          :title="auth.user.email"
        >
          <UserAvatar
            :first-name="auth.user.first_name"
            :last-name="auth.user.last_name"
            :email="auth.user.email"
          />
          <span class="app-shell__user-name">{{ displayName }}</span>
        </RouterLink>
        <button
          type="button"
          class="btn btn--ghost btn--sm"
          @click="onLogout"
        >
          <span>{{ t('nav.logout') }}</span>
        </button>
      </div>
    </header>

    <main class="app-shell__main">
      <RouterView />
    </main>
  </div>
</template>
