import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'legatio.theme'

function systemPrefersDark(): boolean {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

function resolveInitialTheme(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  return systemPrefersDark() ? 'dark' : 'light'
}

function applyTheme(mode: ThemeMode): void {
  document.documentElement.setAttribute('data-theme', mode)
}

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<ThemeMode>(resolveInitialTheme())
  applyTheme(theme.value)

  function setTheme(mode: ThemeMode): void {
    theme.value = mode
    localStorage.setItem(STORAGE_KEY, mode)
    applyTheme(mode)
  }

  function toggleTheme(): void {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return {
    theme,
    setTheme,
    toggleTheme,
  }
})
