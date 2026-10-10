import { watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { type AppLocale, persistLocale } from '@/i18n'
import { useLocaleStore } from '@/stores/locale'

export function useLocaleSwitch() {
  const store = useLocaleStore()
  const { locale: i18nLocale } = useI18n()

  function setLocale(next: AppLocale): void {
    store.setLocale(next)
    i18nLocale.value = next
    persistLocale(next)
  }

  watch(
    () => store.locale,
    (value) => {
      i18nLocale.value = value
    },
    { immediate: true },
  )

  return {
    locale: store.locale,
    setLocale,
    supported: store.supported,
  }
}
