<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { useThemeStore } from '@/stores/theme'

const { t } = useI18n()
const themeStore = useThemeStore()

function setLight(): void {
  themeStore.setTheme('light')
}

function setDark(): void {
  themeStore.setTheme('dark')
}
</script>

<template>
  <div
    class="theme-switch"
    role="group"
    :aria-label="t('common.theme')"
  >
    <button
      type="button"
      class="theme-switch__btn"
      :class="{ 'is-active': themeStore.theme === 'light' }"
      :aria-pressed="themeStore.theme === 'light'"
      :title="t('common.light')"
      @click="setLight"
    >
      {{ t('common.lightShort') }}
    </button>
    <button
      type="button"
      class="theme-switch__btn"
      :class="{ 'is-active': themeStore.theme === 'dark' }"
      :aria-pressed="themeStore.theme === 'dark'"
      :title="t('common.dark')"
      @click="setDark"
    >
      {{ t('common.darkShort') }}
    </button>
  </div>
</template>
