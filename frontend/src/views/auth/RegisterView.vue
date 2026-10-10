<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import LocaleSwitch from '@/components/common/LocaleSwitch.vue'
import ThemeSwitch from '@/components/common/ThemeSwitch.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  first_name: '',
  last_name: '',
})
const localError = ref<string | null>(null)

async function onSubmit(): Promise<void> {
  localError.value = null

  if (form.password.length < 8) {
    localError.value = t('auth.passwordMin')
    return
  }
  if (form.password !== form.confirmPassword) {
    localError.value = t('auth.passwordMismatch')
    return
  }

  try {
    await auth.register({
      email: form.email.trim(),
      password: form.password,
      first_name: form.first_name.trim() || undefined,
      last_name: form.last_name.trim() || undefined,
    })
    await router.replace({ name: 'dashboard' })
  } catch {
    localError.value = auth.errorMessage || t('auth.registerFailed')
  }
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

      <h1 class="auth-layout__title">
        {{ t('auth.registerTitle') }}
      </h1>
      <p class="auth-layout__subtitle">
        {{ t('auth.registerSubtitle') }}
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
        @submit.prevent="onSubmit"
      >
        <div class="form-field">
          <label
            class="form-label"
            for="reg-first"
          >{{ t('auth.firstName') }}</label>
          <input
            id="reg-first"
            v-model="form.first_name"
            class="form-input"
            type="text"
            autocomplete="given-name"
          >
        </div>

        <div class="form-field">
          <label
            class="form-label"
            for="reg-last"
          >{{ t('auth.lastName') }}</label>
          <input
            id="reg-last"
            v-model="form.last_name"
            class="form-input"
            type="text"
            autocomplete="family-name"
          >
        </div>

        <div class="form-field">
          <label
            class="form-label"
            for="reg-email"
          >{{ t('auth.email') }}</label>
          <input
            id="reg-email"
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
            for="reg-password"
          >{{ t('auth.password') }}</label>
          <input
            id="reg-password"
            v-model="form.password"
            class="form-input"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
          >
        </div>

        <div class="form-field">
          <label
            class="form-label"
            for="reg-confirm"
          >{{ t('auth.confirmPassword') }}</label>
          <input
            id="reg-confirm"
            v-model="form.confirmPassword"
            class="form-input"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
          >
        </div>

        <button
          class="btn btn--primary btn--block"
          type="submit"
          :disabled="auth.loading"
        >
          {{ auth.loading ? t('auth.registering') : t('auth.submitRegister') }}
        </button>
      </form>

      <div class="auth-layout__footer">
        {{ t('auth.hasAccount') }}
        <RouterLink :to="{ name: 'login' }">
          {{ t('auth.goLogin') }}
        </RouterLink>
      </div>
    </div>
  </div>
</template>
