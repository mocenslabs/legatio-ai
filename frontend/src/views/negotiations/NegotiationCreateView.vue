<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as agentsApi from '@/api/agents'
import * as constitutionsApi from '@/api/constitutions'
import * as negotiationsApi from '@/api/negotiations'
import type { Agent, Constitution } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'

const { t } = useI18n()
const router = useRouter()

const agents = ref<Agent[]>([])
const constitutions = ref<Constitution[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const form = reactive({
  title: '',
  user_instruction: '',
  user_agent_id: '',
  external_agent_id: '',
  constitution_id: '',
  max_rounds: 10,
})

async function loadOptions(): Promise<void> {
  try {
    const [allAgents, allConsts] = await Promise.all([
      agentsApi.listAgents(),
      constitutionsApi.listConstitutions(),
    ])
    agents.value = allAgents
    constitutions.value = allConsts

    const userAgents = allAgents.filter((a) =>
      String(a.agent_type).toUpperCase().includes('USER'),
    )
    const external = allAgents.filter((a) =>
      !String(a.agent_type).toUpperCase().includes('USER'),
    )

    form.user_agent_id = userAgents[0]?.id || allAgents[0]?.id || ''
    form.external_agent_id = external[0]?.id || allAgents[1]?.id || ''
    form.constitution_id = allConsts[0]?.id || ''
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  }
}

async function onSubmit(): Promise<void> {
  error.value = null
  if (!form.title.trim() || !form.user_agent_id || !form.external_agent_id || !form.constitution_id) {
    error.value = t('negotiations.formRequired')
    return
  }
  loading.value = true
  try {
    const created = await negotiationsApi.createNegotiation({
      title: form.title.trim(),
      user_instruction: form.user_instruction.trim() || form.title.trim(),
      user_agent_id: form.user_agent_id,
      external_agent_id: form.external_agent_id,
      constitution_id: form.constitution_id,
      max_rounds: form.max_rounds,
    })
    await router.replace({ name: 'negotiation-detail', params: { id: created.id } })
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadOptions()
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-header__title">
          {{ t('negotiations.create') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('negotiations.createSubtitle') }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          @click="router.push({ name: 'negotiations' })"
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
            for="n-title"
          >{{ t('negotiations.colTitle') }}</label>
          <input
            id="n-title"
            v-model="form.title"
            class="form-input"
            required
          >
        </div>
        <div class="form-field">
          <label
            class="form-label"
            for="n-instr"
          >{{ t('negotiations.instruction') }}</label>
          <textarea
            id="n-instr"
            v-model="form.user_instruction"
            class="form-textarea"
          />
        </div>
        <div class="form-row form-row--2">
          <div class="form-field">
            <label
              class="form-label"
              for="n-user-agent"
            >{{ t('negotiations.userAgent') }}</label>
            <select
              id="n-user-agent"
              v-model="form.user_agent_id"
              class="form-select"
              required
            >
              <option
                v-for="a in agents"
                :key="a.id"
                :value="a.id"
              >
                {{ a.name }}
              </option>
            </select>
          </div>
          <div class="form-field">
            <label
              class="form-label"
              for="n-ext-agent"
            >{{ t('negotiations.externalAgent') }}</label>
            <select
              id="n-ext-agent"
              v-model="form.external_agent_id"
              class="form-select"
              required
            >
              <option
                v-for="a in agents"
                :key="a.id"
                :value="a.id"
              >
                {{ a.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="form-row form-row--2">
          <div class="form-field">
            <label
              class="form-label"
              for="n-const"
            >{{ t('nav.constitutions') }}</label>
            <select
              id="n-const"
              v-model="form.constitution_id"
              class="form-select"
              required
            >
              <option
                v-for="c in constitutions"
                :key="c.id"
                :value="c.id"
              >
                {{ c.name }}
              </option>
            </select>
          </div>
          <div class="form-field">
            <label
              class="form-label"
              for="n-rounds"
            >{{ t('negotiations.maxRounds') }}</label>
            <input
              id="n-rounds"
              v-model.number="form.max_rounds"
              class="form-input"
              type="number"
              min="1"
              max="50"
            >
          </div>
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
