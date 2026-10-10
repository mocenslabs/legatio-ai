import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from '@/App.vue'
import { i18n } from '@/i18n'
import router from '@/router'
import { useThemeStore } from '@/stores/theme'

import '@/assets/styles/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(i18n)

// Apply persisted theme before mount paint
useThemeStore(pinia)

app.mount('#app')
