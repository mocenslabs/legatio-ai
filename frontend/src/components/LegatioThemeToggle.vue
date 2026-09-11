<script setup lang="ts">
import { Moon, Sun } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/composables/useTheme'

const { theme, toggleTheme } = useTheme()
</script>

<template>
  <Button variant="ghost" size="icon" :aria-label="'Toggle theme'" @click="toggleTheme">
    <Sun v-if="theme === 'dark'" class="h-5 w-5 text-accent transition-all" />
    <Moon v-else class="h-5 w-5 text-primary transition-all" />
  </Button>
</template>
