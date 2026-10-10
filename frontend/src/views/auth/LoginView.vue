<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import LocaleSwitch from '@/components/common/LocaleSwitch.vue'
import ThemeSwitch from '@/components/common/ThemeSwitch.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '', code: '' })
const step = ref<'credentials' | '2fa'>('credentials')
const localError = ref<string | null>(null)

async function onSubmitCredentials(): Promise<void> {
  localError.value = null
  try {
    const result = await auth.login({
      email: form.email.trim(),
      password: form.password,
    })
    if (result === 'requires_2fa') {
      step.value = '2fa'
      return
    }
    await goApp()
  } catch {
    localError.value = auth.errorMessage || t('auth.invalidCredentials')
  }
}

async function onSubmit2fa(): Promise<void> {
  localError.value = null
  try {
    await auth.verify2faLogin(form.code.trim())
    await goApp()
  } catch {
    localError.value = auth.errorMessage || t('auth.invalid2fa')
  }
}

async function goApp(): Promise<void> {
  const redirect =
    typeof route.query.redirect === 'string' ? route.query.redirect : '/app/dashboard'
  await router.replace(redirect)
}

function backToCredentials(): void {
  step.value = 'credentials'
  form.code = ''
  auth.pending2fa = null
}
</script>

<template>
  <div class="auth-layout">
    <div class="auth-layout__card">
      <div class="auth-layout__toolbar">
        <ThemeSwitch />
        <LocaleSwitch />
      </div>

      <div class="auth-layout__brand">
        <div class="auth-layout__logo">
          {{ t('app.name') }}
        </div>
        <div class="auth-layout__tagline">
          {{ t('app.tagline') }}
        </div>
      </div>

      <template v-if="step === 'credentials'">
        <h1 class="auth-layout__title">
          {{ t('auth.loginTitle') }}
        </h1>
        <p class="auth-layout__subtitle">
          {{ t('auth.loginSubtitle') }}
        </p>
        <div
          v-if="localError"
          class="form-alert"
          role="alert"
        >
          {{ localError }}
        </div>
        <form
          class="auth-layout__form"
          @submit.prevent="onSubmitCredentials"
        >
          <div class="form-field">
            <label
              class="form-label"
              for="login-email"
            >{{ t('auth.email') }}</label>
            <input
              id="login-email"
              v-model="form.email"
              class="form-input"
              type="email"
              autocomplete="username"
              required
            >
          </div>
          <div class="form-field">
            <label
              class="form-label"
              for="login-password"
            >{{ t('auth.password') }}</label>
            <input
              id="login-password"
              v-model="form.password"
              class="form-input"
              type="password"
              autocomplete="current-password"
              required
              minlength="8"
            >
          </div>
          <button
            class="btn btn--primary btn--block"
            type="submit"
            :disabled="auth.loading"
          >
            {{ auth.loading ? t('auth.loggingIn') : t('auth.submitLogin') }}
          </button>
        </form>
        <div class="auth-layout__footer">
          {{ t('auth.noAccount') }}
          <RouterLink :to="{ name: 'register' }">
            {{ t('auth.goRegister') }}
          </RouterLink>
        </div>
      </template>

      <template v-else>
        <h1 class="auth-layout__title">
          {{ t('auth.twoFactorTitle') }}
        </h1>
        <p class="auth-layout__subtitle">
          {{ t('auth.twoFactorSubtitle') }}
        </p>
        <div
          v-if="localError"
          class="form-alert"
          role="alert"
        >
          {{ localError }}
        </div>
        <form
          class="auth-layout__form"
          @submit.prevent="onSubmit2fa"
        >
          <div class="form-field">
            <label
              class="form-label"
              for="login-2fa"
            >{{ t('auth.totpCode') }}</label>
            <input
              id="login-2fa"
              v-model="form.code"
              class="form-input"
              inputmode="numeric"
              pattern="[0-9]{6}"
              maxlength="6"
              required
              autocomplete="one-time-code"
            >
          </div>
          <button
            class="btn btn--primary btn--block"
            type="submit"
            :disabled="auth.loading"
          >
            {{ auth.loading ? t('auth.verifying') : t('auth.verify2fa') }}
          </button>
          <button
            type="button"
            class="btn btn--ghost btn--block"
            @click="backToCredentials"
          >
            {{ t('common.back') }}
          </button>
        </form>
      </template>
    </div>
  </div>
</template>
