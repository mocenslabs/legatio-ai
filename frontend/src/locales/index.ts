import { createI18n } from 'vue-i18n'
import enAuth from './en/auth.json'
import enCommon from './en/common.json'
import enConstitution from './en/constitution.json'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      auth: enAuth,
      common: enCommon,
      constitution: enConstitution,
    },
  },
  missingWarn: false,
  fallbackWarn: false,
})

export default i18n
