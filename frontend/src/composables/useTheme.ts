import { ref, onMounted, watch } from 'vue'

export function useTheme() {
  const theme = ref<'light' | 'dark'>('dark')

  onMounted(() => {
    const savedTheme = localStorage.getItem('legatio-theme') as 'light' | 'dark'
    if (savedTheme) {
      theme.value = savedTheme
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      theme.value = 'dark'
    }
    applyTheme()
  })

  watch(theme, (newTheme) => {
    localStorage.setItem('legatio-theme', newTheme)
    applyTheme()
  })

  function applyTheme() {
    if (theme.value === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return { theme, toggleTheme }
}
