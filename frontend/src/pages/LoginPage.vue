<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/api/client'
import { getApiErrorMessage, getErrorStatus } from '@/utils/api'
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

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

// Form state
const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

async function handleLogin() {
  if (!email.value || !password.value) {
    errorMessage.value = t('auth.login.errors.required')
    return
  }

  isLoading.value = true
  errorMessage.value = null

  try {
    // Ajusta el endpoint al real de tu backend Django (ej: /auth/login/)
    const response = await apiClient.post('/auth/login/', {
      email: email.value,
      password: password.value,
    })

    const { access, refresh, user } = response.data

    // Guardar en Pinia (el interceptor de Axios ahora ya puede usar el access token)
    authStore.setTokens(access, refresh)
    authStore.setUser(user)

    // Redirigir a la ruta original o al dashboard
    const redirectPath = (route.query.redirect as string) || '/dashboard'
    await router.push(redirectPath)
  } catch (error: unknown) {
    const status = getErrorStatus(error)
    if (status === 401) {
      errorMessage.value = t('auth.login.errors.invalidCredentials')
    } else {
      errorMessage.value = getApiErrorMessage(error, t('auth.login.errors.generic'))
    }
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
          {{ t('auth.login.title') }}
        </CardTitle>
        <CardDescription class="text-muted-foreground">
          {{ t('auth.login.subtitle') }}
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form class="space-y-4" @submit.prevent="handleLogin">
          <!-- Error Alert -->
          <Alert
            v-if="errorMessage"
            variant="destructive"
            class="bg-destructive/10 text-destructive border-destructive/20"
          >
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>
              {{ errorMessage }}
            </AlertDescription>
          </Alert>

          <!-- Email Field -->
          <div class="space-y-2">
            <Label for="email">{{ t('auth.login.email') }}</Label>
            <Input
              id="email"
              v-model="email"
              type="email"
              :placeholder="t('auth.login.emailPlaceholder')"
              autocomplete="email"
              required
              :disabled="isLoading"
              class="transition-all focus-visible:ring-primary"
            />
          </div>

          <!-- Password Field -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <Label for="password">{{ t('auth.login.password') }}</Label>
              <router-link
                to="/forgot-password"
                class="text-xs text-primary hover:text-primary/80 underline-offset-4 hover:underline transition-colors"
              >
                {{ t('auth.login.forgotPassword') }}
              </router-link>
            </div>
            <Input
              id="password"
              v-model="password"
              type="password"
              :placeholder="t('auth.login.passwordPlaceholder')"
              autocomplete="current-password"
              required
              :disabled="isLoading"
              class="transition-all focus-visible:ring-primary"
            />
          </div>

          <!-- Submit Button -->
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
              {{ t('auth.login.submitting') }}
            </span>
            <span v-else>
              {{ t('auth.login.submit') }}
            </span>
          </Button>
        </form>
      </CardContent>

      <CardFooter class="flex flex-col space-y-4 border-t bg-muted/30 px-6 py-4">
        <div class="text-sm text-center text-muted-foreground">
          {{ t('auth.login.noAccount') }}
          <router-link
            to="/register"
            class="font-medium text-primary hover:text-primary/80 underline-offset-4 hover:underline transition-colors"
          >
            {{ t('auth.login.signUp') }}
          </router-link>
        </div>

        <!-- Trust badge (UX detail for Legatio) -->
        <div class="flex items-center justify-center gap-1.5 text-xs text-muted-foreground/60 pt-2">
          <ShieldCheck class="h-3.5 w-3.5" />
          <span>Secured by Legatio Policy Engine</span>
        </div>
      </CardFooter>
    </Card>
  </div>
</template>
