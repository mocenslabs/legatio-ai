/**
 * Application entry point.
 *
 * Registers global plugins: router, Pinia, Vue Query.
 *
 * Reference: 02-ARCHITECTURE.md Section 5.2
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'

import App from './App.vue'
import router from './router'
import './assets/styles/main.css'

const app = createApp(App)

// Install plugins
app.use(createPinia())
app.use(router)
app.use(VueQueryPlugin)

// Mount the application
app.mount('#app')
