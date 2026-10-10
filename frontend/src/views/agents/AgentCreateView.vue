<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as agentsApi from '@/api/agents'
import { extractApiMessage } from '@/utils/errors'

const { t } = useI18n()
const router = useRouter()

const loading = ref(false)
const error = ref<string | null>(null)

const form = reactive({
  name: '',
  description: '',
})

async function onSubmit(): Promise<void> {
  error.value = null
  if (!form.name.trim()) {
    error.value = t('agents.nameRequired')
    return
  }
  loading.value = true
  try {
    await agentsApi.createAgent({
      name: form.name.trim(),
      description: form.description.trim() || undefined,
    })
    await router.replace({ name: 'agents' })
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-header__title">
          {{ t('agents.create') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('agents.createSubtitle') }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          @click="router.push({ name: 'agents' })"
        >
          {{ t('common.cancel') }}
        </button>
      </div>
    </div>

    <div
      v-if="error"
      class="form-alert"
      role="alert"
    >
      {{ error }}
    </div>

    <div class="card-panel">
      <form
        class="card-panel__body stack"
        @submit.prevent="onSubmit"
      >
        <div class="form-field">
          <label
            class="form-label"
            for="a-name"
          >{{ t('agents.colName') }}</label>
          <input
            id="a-name"
            v-model="form.name"
            class="form-input"
            required
            maxlength="100"
          >
        </div>
        <div class="form-field">
          <label
            class="form-label"
            for="a-desc"
          >{{ t('agents.description') }}</label>
          <textarea
            id="a-desc"
            v-model="form.description"
            class="form-textarea"
          />
        </div>
        <p class="page-header__subtitle">
          {{ t('agents.createHint') }}
        </p>
        <button
          class="btn btn--primary"
          type="submit"
          :disabled="loading"
        >
          {{ loading ? t('common.saving') : t('common.save') }}
        </button>
      </form>
    </div>
  </div>
</template>
