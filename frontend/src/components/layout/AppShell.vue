<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import LocaleSwitch from '@/components/common/LocaleSwitch.vue'
import ThemeSwitch from '@/components/common/ThemeSwitch.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'
import { displayNameFromUser } from '@/utils/avatar'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const sidebarOpen = ref(false)

const navItems = computed(() => [
  { name: 'dashboard', label: t('nav.dashboard'), to: { name: 'dashboard' } },
  { name: 'agents', label: t('nav.agents'), to: { name: 'agents' } },
  { name: 'constitutions', label: t('nav.constitutions'), to: { name: 'constitutions' } },
  { name: 'negotiations', label: t('nav.negotiations'), to: { name: 'negotiations' } },
  { name: 'approvals', label: t('nav.approvals'), to: { name: 'approvals' } },
  { name: 'agreements', label: t('nav.agreements'), to: { name: 'agreements' } },
  { name: 'audit', label: t('nav.audit'), to: { name: 'audit' } },
  { name: 'help', label: t('nav.help'), to: { name: 'help' } },
  { name: 'profile', label: t('nav.profile'), to: { name: 'profile' } },
])

const pageTitle = computed(() => {
  const key = route.meta.titleKey as string | undefined
  if (key) return t(key)
  return t('app.name')
})

const displayName = computed(() =>
  displayNameFromUser({
    first_name: auth.user?.first_name,
    last_name: auth.user?.last_name,
    email: auth.user?.email,
  }),
)

const avatarSeed = computed(() => auth.user?.id || auth.user?.email || 'user')

watch(
  () => route.fullPath,
  () => {
    sidebarOpen.value = false
  },
)

function toggleSidebar(): void {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar(): void {
  sidebarOpen.value = false
}

function onLogout(): void {
  auth.logout()
  void router.push({ name: 'home' })
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
      <RouterLink
        :to="{ name: 'home' }"
        class="app-shell__brand"
      >
        {{ t('app.name') }}
      </RouterLink>
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
          {{ item.label }}
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
          class="user-menu"
          :title="t('nav.profile')"
        >
          <UserAvatar
            :seed="avatarSeed"
            :first-name="auth.user.first_name"
            :last-name="auth.user.last_name"
            :email="auth.user.email"
            size="sm"
          />
          <span class="user-menu__name">{{ displayName }}</span>
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
