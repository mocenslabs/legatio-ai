import { createI18n } from 'vue-i18n'
import enAuth from './en/auth.json'
import enCommon from './en/common.json'

const i18n = createI18n({
  legacy: false, // Composition API
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      // CORREGIDO: enAuth ya es { login: { title: "..." } }
      // No necesita .auth al final
      auth: enAuth,
      common: enCommon,
    },
  },
  missingWarn: false,
  fallbackWarn: false,
})

export default i18n
