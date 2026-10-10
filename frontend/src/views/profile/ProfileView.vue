<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import * as authApi from '@/api/auth'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'
import type { TwoFactorSetupResponse } from '@/types/auth'
import { displayNameFromUser } from '@/utils/avatar'
import { extractApiMessage } from '@/utils/errors'

const { t } = useI18n()
const auth = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const profileForm = reactive({
  first_name: '',
  last_name: '',
  preferred_language: 'en',
  preferred_timezone: 'UTC',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm: '',
})

const setup = ref<TwoFactorSetupResponse | null>(null)
const totpCode = ref('')
const disableCode = ref('')

async function load(): Promise<void> {
  error.value = null
  try {
    await auth.refreshProfile()
    const u = auth.user
    if (u) {
      profileForm.first_name = u.first_name || ''
      profileForm.last_name = u.last_name || ''
      profileForm.preferred_language = u.preferred_language || 'en'
      profileForm.preferred_timezone = u.preferred_timezone || 'UTC'
    }
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  }
}

async function saveProfile(): Promise<void> {
  error.value = null
  success.value = null
  loading.value = true
  try {
    await auth.updateProfile({
      first_name: profileForm.first_name.trim(),
      last_name: profileForm.last_name.trim(),
      preferred_language: profileForm.preferred_language,
      preferred_timezone: profileForm.preferred_timezone,
    })
    success.value = t('profile.saved')
  } catch (err) {
    error.value = extractApiMessage(err, t('profile.saveFailed'))
  } finally {
    loading.value = false
  }
}

async function savePassword(): Promise<void> {
  error.value = null
  success.value = null
  if (passwordForm.new_password.length < 8) {
    error.value = t('auth.passwordMin')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm) {
    error.value = t('auth.passwordMismatch')
    return
  }
  loading.value = true
  try {
    await authApi.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm = ''
    success.value = t('profile.passwordChanged')
  } catch (err) {
    error.value = extractApiMessage(err, t('profile.passwordFailed'))
  } finally {
    loading.value = false
  }
}

async function start2fa(): Promise<void> {
  error.value = null
  success.value = null
  loading.value = true
  try {
    setup.value = await authApi.enable2fa()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

async function confirm2fa(): Promise<void> {
  error.value = null
  success.value = null
  loading.value = true
  try {
    await authApi.confirm2fa(totpCode.value.trim())
    setup.value = null
    totpCode.value = ''
    await auth.refreshProfile()
    success.value = t('profile.twoFactorEnabled')
  } catch (err) {
    error.value = extractApiMessage(err, t('auth.invalid2fa'))
  } finally {
    loading.value = false
  }
}

async function disable2fa(): Promise<void> {
  error.value = null
  success.value = null
  loading.value = true
  try {
    await authApi.disable2fa(disableCode.value.trim())
    disableCode.value = ''
    await auth.refreshProfile()
    success.value = t('profile.twoFactorDisabled')
  } catch (err) {
    error.value = extractApiMessage(err, t('auth.invalid2fa'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-header__title">
          {{ t('profile.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('profile.subtitle') }}
        </p>
      </div>
    </div>

    <div
      v-if="error"
      class="form-alert"
      role="alert"
    >
      {{ error }}
    </div>
    <div
      v-if="success"
      class="form-alert form-alert--success"
      role="status"
    >
      {{ success }}
    </div>

    <div class="stack">
      <div class="card-panel">
        <div class="card-panel__body">
          <div class="profile-hero">
            <UserAvatar
              v-if="auth.user"
              :seed="auth.user.id || auth.user.email"
              :first-name="auth.user.first_name"
              :last-name="auth.user.last_name"
              :email="auth.user.email"
              size="lg"
            />
            <div class="profile-hero__meta">
              <p class="profile-hero__name">
                {{
                  displayNameFromUser({
                    first_name: auth.user?.first_name,
                    last_name: auth.user?.last_name,
                    email: auth.user?.email,
                  })
                }}
              </p>
              <p class="profile-hero__email">
                {{ auth.user?.email }}
              </p>
              <p class="page-header__subtitle">
                {{ t('profile.avatarHint') }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('profile.accountSection') }}
        </div>
        <form
          class="card-panel__body stack"
          @submit.prevent="saveProfile"
        >
          <div class="meta-grid">
            <div class="meta-item">
              <div class="meta-item__label">
                2FA
              </div>
              <div class="meta-item__value">
                <span
                  class="badge"
                  :class="auth.user?.two_factor_enabled ? 'badge--success' : 'badge--neutral'"
                >
                  {{
                    auth.user?.two_factor_enabled ? t('profile.twoFactorOn') : t('profile.twoFactorOff')
                  }}
                </span>
              </div>
            </div>
          </div>
          <div class="form-row form-row--2">
            <div class="form-field">
              <label
                class="form-label"
                for="p-first"
              >{{ t('auth.firstName') }}</label>
              <input
                id="p-first"
                v-model="profileForm.first_name"
                class="form-input"
                type="text"
              >
            </div>
            <div class="form-field">
              <label
                class="form-label"
                for="p-last"
              >{{ t('auth.lastName') }}</label>
              <input
                id="p-last"
                v-model="profileForm.last_name"
                class="form-input"
                type="text"
              >
            </div>
          </div>
          <div class="form-row form-row--2">
            <div class="form-field">
              <label
                class="form-label"
                for="p-lang"
              >{{ t('profile.language') }}</label>
              <select
                id="p-lang"
                v-model="profileForm.preferred_language"
                class="form-select"
              >
                <option value="en">
                  English
                </option>
                <option value="es">
                  Español
                </option>
              </select>
            </div>
            <div class="form-field">
              <label
                class="form-label"
                for="p-tz"
              >{{ t('profile.timezone') }}</label>
              <input
                id="p-tz"
                v-model="profileForm.preferred_timezone"
                class="form-input"
                type="text"
              >
            </div>
          </div>
          <button
            class="btn btn--primary"
            type="submit"
            :disabled="loading"
          >
            {{ loading ? t('common.saving') : t('profile.saveProfile') }}
          </button>
        </form>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('profile.passwordSection') }}
        </div>
        <form
          class="card-panel__body stack"
          @submit.prevent="savePassword"
        >
          <p class="page-header__subtitle">
            {{ t('profile.passwordHint') }}
          </p>
          <div class="form-field">
            <label
              class="form-label"
              for="p-cur"
            >{{ t('profile.currentPassword') }}</label>
            <input
              id="p-cur"
              v-model="passwordForm.current_password"
              class="form-input"
              type="password"
              required
              autocomplete="current-password"
            >
          </div>
          <div class="form-row form-row--2">
            <div class="form-field">
              <label
                class="form-label"
                for="p-new"
              >{{ t('profile.newPassword') }}</label>
              <input
                id="p-new"
                v-model="passwordForm.new_password"
                class="form-input"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
              >
            </div>
            <div class="form-field">
              <label
                class="form-label"
                for="p-conf"
              >{{ t('auth.confirmPassword') }}</label>
              <input
                id="p-conf"
                v-model="passwordForm.confirm"
                class="form-input"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
              >
            </div>
          </div>
          <button
            class="btn btn--secondary"
            type="submit"
            :disabled="loading"
          >
            {{ t('profile.changePassword') }}
          </button>
        </form>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('profile.twoFactorSection') }}
        </div>
        <div class="card-panel__body stack">
          <template v-if="!auth.user?.two_factor_enabled">
            <p class="page-header__subtitle">
              {{ t('profile.twoFactorHint') }}
            </p>
            <button
              v-if="!setup"
              type="button"
              class="btn btn--primary"
              :disabled="loading"
              @click="start2fa"
            >
              {{ t('profile.enable2fa') }}
            </button>
            <template v-else>
              <p class="page-header__subtitle">
                {{ t('profile.scanQr') }}
              </p>
              <img
                v-if="setup.qr_code_url"
                :src="setup.qr_code_url"
                alt="QR 2FA"
                width="200"
                height="200"
              >
              <div class="meta-item">
                <div class="meta-item__label">
                  {{ t('profile.secret') }}
                </div>
                <div class="meta-item__value">
                  {{ setup.secret }}
                </div>
              </div>
              <div class="form-field">
                <label
                  class="form-label"
                  for="p-totp"
                >{{ t('auth.totpCode') }}</label>
                <input
                  id="p-totp"
                  v-model="totpCode"
                  class="form-input"
                  maxlength="6"
                  inputmode="numeric"
                >
              </div>
              <button
                type="button"
                class="btn btn--primary"
                :disabled="loading"
                @click="confirm2fa"
              >
                {{ t('profile.confirm2fa') }}
              </button>
            </template>
          </template>
          <template v-else>
            <p class="page-header__subtitle">
              {{ t('profile.disable2faHint') }}
            </p>
            <div class="form-field">
              <label
                class="form-label"
                for="p-dis"
              >{{ t('auth.totpCode') }}</label>
              <input
                id="p-dis"
                v-model="disableCode"
                class="form-input"
                maxlength="6"
                inputmode="numeric"
              >
            </div>
            <button
              type="button"
              class="btn btn--danger"
              :disabled="loading"
              @click="disable2fa"
            >
              {{ t('profile.disable2fa') }}
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
