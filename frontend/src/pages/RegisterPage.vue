<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiClient } from '@/api/client'

// UI Components
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, ShieldCheck } from '@lucide/vue'
import LegatioLogo from '@/components/LegatioLogo.vue'

const router = useRouter()
const { t } = useI18n()

// Form state
const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

async function handleRegister() {
  if (!fullName.value || !email.value || !password.value || !confirmPassword.value) {
    errorMessage.value = t('auth.register.errors.required')
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMessage.value = t('auth.register.errors.passwordMismatch')
    return
  }

  isLoading.value = true
  errorMessage.value = null

  try {
    await apiClient.post('/auth/register/', {
      first_name: fullName.value.split(' ')[0],
      last_name: fullName.value.split(' ').slice(1).join(' ') || '',
      email: email.value,
      password: password.value,
    })

    // Redirigir al login para que inicien sesión (o auto-login si el backend lo permite)
    await router.push('/login?registered=true')
  } catch (error: any) {
    console.error('Register failed:', error)
    errorMessage.value = error.response?.data?.detail || t('auth.register.errors.generic')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen w-full items-center justify-center bg-background p-4">
    <Card class="w-full max-w-md border-border shadow-sm">
      <CardHeader class="space-y-1 text-center">
        <div class="flex justify-center mb-4">
          <LegatioLogo />
        </div>
        <CardTitle class="text-2xl font-semibold tracking-tight">
          {{ t('auth.register.title') }}
        </CardTitle>
        <CardDescription class="text-muted-foreground">
          {{ t('auth.register.subtitle') }}
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form class="space-y-4" @submit.prevent="handleRegister">
          <Alert
            v-if="errorMessage"
            variant="destructive"
            class="bg-destructive/10 text-destructive border-destructive/20"
          >
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>{{ errorMessage }}</AlertDescription>
          </Alert>

          <div class="space-y-2">
            <Label for="fullName">{{ t('auth.register.fullName') }}</Label>
            <Input
              id="fullName"
              v-model="fullName"
              type="text"
              :placeholder="t('auth.register.fullNamePlaceholder')"
              :disabled="isLoading"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="email">{{ t('auth.register.email') }}</Label>
            <Input
              id="email"
              v-model="email"
              type="email"
              :placeholder="t('auth.register.emailPlaceholder')"
              :disabled="isLoading"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="password">{{ t('auth.register.password') }}</Label>
            <Input
              id="password"
              v-model="password"
              type="password"
              :placeholder="t('auth.register.passwordPlaceholder')"
              :disabled="isLoading"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="confirmPassword">{{ t('auth.register.confirmPassword') }}</Label>
            <Input
              id="confirmPassword"
              v-model="confirmPassword"
              type="password"
              :placeholder="t('auth.register.passwordPlaceholder')"
              :disabled="isLoading"
              required
            />
          </div>

          <Button type="submit" class="w-full mt-6" :disabled="isLoading">
            <span v-if="isLoading" class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                  fill="none"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ t('auth.register.submitting') }}
            </span>
            <span v-else>{{ t('auth.register.submit') }}</span>
          </Button>
        </form>
      </CardContent>

      <CardFooter class="flex flex-col space-y-4 border-t bg-muted/30 px-6 py-4">
        <div class="text-sm text-center text-muted-foreground">
          {{ t('auth.register.hasAccount') }}
          <router-link
            to="/login"
            class="font-medium text-primary hover:text-primary/80 underline-offset-4 hover:underline transition-colors"
          >
            {{ t('auth.register.signIn') }}
          </router-link>
        </div>
        <div class="flex items-center justify-center gap-1.5 text-xs text-muted-foreground/60 pt-2">
          <ShieldCheck class="h-3.5 w-3.5" />
          <span>Secured by Legatio Policy Engine</span>
        </div>
      </CardFooter>
    </Card>
  </div>
</template>
