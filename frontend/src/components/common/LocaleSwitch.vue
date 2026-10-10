<script setup lang="ts">
import { useLocaleSwitch } from '@/composables/useLocaleSwitch'
import type { AppLocale } from '@/i18n'

const { locale, setLocale, supported } = useLocaleSwitch()

function onSelect(code: AppLocale): void {
  setLocale(code)
}
</script>

<template>
  <div
    class="locale-switch"
    role="group"
    :aria-label="$t('common.language')"
  >
    <button
      v-for="code in supported"
      :key="code"
      type="button"
      class="locale-switch__btn"
      :class="{ 'is-active': locale === code }"
      :aria-pressed="locale === code"
      @click="onSelect(code)"
    >
      {{ code }}
    </button>
  </div>
</template>
