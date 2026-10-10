import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  type AppLocale,
  persistLocale,
  resolveInitialLocale,
  SUPPORTED_LOCALES,
} from '@/i18n'

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref<AppLocale>(resolveInitialLocale())

  function setLocale(next: AppLocale): void {
    if (!SUPPORTED_LOCALES.includes(next)) return
    locale.value = next
    persistLocale(next)
  }

  return {
    locale,
    setLocale,
    supported: SUPPORTED_LOCALES,
  }
})

/** Bridge Pinia locale → vue-i18n instance (call from components). */
export function syncI18nLocale(locale: AppLocale): void {
  const { locale: i18nLocale } = useI18n()
  i18nLocale.value = locale
  persistLocale(locale)
}
