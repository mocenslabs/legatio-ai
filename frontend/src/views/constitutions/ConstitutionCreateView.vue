<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as agentsApi from '@/api/agents'
import * as constitutionsApi from '@/api/constitutions'
import type { Agent } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'

const { t } = useI18n()
const router = useRouter()

const agents = ref<Agent[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const form = reactive({
  name: '',
  description: '',
  agent_id: '',
})

async function loadAgents(): Promise<void> {
  try {
    const all = await agentsApi.listAgents()
    agents.value = all.filter((a) => a.agent_type === 'USER_AGENT' || a.agent_type === 'user_agent')
    if (!agents.value.length) agents.value = all
    if (agents.value[0] && !form.agent_id) form.agent_id = agents.value[0].id
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  }
}

async function onSubmit(): Promise<void> {
  error.value = null
  if (!form.name.trim() || !form.agent_id) {
    error.value = t('constitutions.formRequired')
    return
  }
  loading.value = true
  try {
    const created = await constitutionsApi.createConstitution({
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      agent_id: form.agent_id,
    })
    await router.replace({ name: 'constitution-detail', params: { id: created.id } })
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadAgents()
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-header__title">
          {{ t('constitutions.create') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('constitutions.createSubtitle') }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          @click="router.push({ name: 'constitutions' })"
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
            for="c-name"
          >{{ t('constitutions.colName') }}</label>
          <input
            id="c-name"
            v-model="form.name"
            class="form-input"
            required
            maxlength="200"
          >
        </div>
        <div class="form-field">
          <label
            class="form-label"
            for="c-desc"
          >{{ t('constitutions.description') }}</label>
          <textarea
            id="c-desc"
            v-model="form.description"
            class="form-textarea"
          />
        </div>
        <div class="form-field">
          <label
            class="form-label"
            for="c-agent"
          >{{ t('constitutions.agent') }}</label>
          <select
            id="c-agent"
            v-model="form.agent_id"
            class="form-select"
            required
          >
            <option
              disabled
              value=""
            >
              {{ t('constitutions.selectAgent') }}
            </option>
            <option
              v-for="a in agents"
              :key="a.id"
              :value="a.id"
            >
              {{ a.name }} ({{ a.agent_type }})
            </option>
          </select>
        </div>
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
