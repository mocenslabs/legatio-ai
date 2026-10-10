import { createI18n } from 'vue-i18n'

import en from './locales/en.json'
import es from './locales/es.json'

export const SUPPORTED_LOCALES = ['en', 'es'] as const
export type AppLocale = (typeof SUPPORTED_LOCALES)[number]

const STORAGE_KEY = 'legatio.locale'

export function resolveInitialLocale(): AppLocale {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'en' || stored === 'es') return stored

  const fromEnv = import.meta.env.VITE_DEFAULT_LOCALE
  if (fromEnv === 'en' || fromEnv === 'es') return fromEnv

  const browser = navigator.language.toLowerCase()
  if (browser.startsWith('es')) return 'es'
  return 'en'
}

export function persistLocale(locale: AppLocale): void {
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale: 'en',
  messages: {
    en,
    es,
  },
})

document.documentElement.lang = i18n.global.locale.value
