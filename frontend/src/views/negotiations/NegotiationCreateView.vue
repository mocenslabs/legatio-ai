<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
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

const userAgents = computed(() =>
  agents.value.filter((a) => String(a.agent_type || '').toUpperCase().includes('USER')),
)
const externalAgents = computed(() =>
  agents.value.filter((a) => !String(a.agent_type || '').toUpperCase().includes('USER')),
)

async function loadOptions(): Promise<void> {
  try {
    const [allAgents, allConsts] = await Promise.all([
      agentsApi.listAgents(),
      constitutionsApi.listConstitutions(),
    ])
    agents.value = allAgents
    constitutions.value = allConsts

    const users = allAgents.filter((a) =>
      String(a.agent_type || '').toUpperCase().includes('USER'),
    )
    const external = allAgents.filter(
      (a) => !String(a.agent_type || '').toUpperCase().includes('USER'),
    )

    form.user_agent_id = users[0]?.id || ''
    form.external_agent_id = external[0]?.id || ''
    form.constitution_id = allConsts[0]?.id || ''
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  }
}

async function onSubmit(): Promise<void> {
  error.value = null
  if (
    !form.title.trim() ||
    !form.user_agent_id ||
    !form.external_agent_id ||
    !form.constitution_id
  ) {
    error.value = t('negotiations.formRequired')
    return
  }
  if (!userAgents.value.length) {
    error.value = t('negotiations.needUserAgent')
    return
  }
  if (!externalAgents.value.length) {
    error.value = t('negotiations.needExternalAgent')
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
      <div class="card-panel__body stack">
        <div class="rules-explainer">
          <p class="rules-explainer__title">
            {{ t('negotiations.createExplainerTitle') }}
          </p>
          <ol class="rules-explainer__list">
            <li>{{ t('negotiations.createExplainer1') }}</li>
            <li>{{ t('negotiations.createExplainer2') }}</li>
            <li>{{ t('negotiations.createExplainer3') }}</li>
          </ol>
        </div>

        <form
          class="stack"
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
              maxlength="200"
              :placeholder="t('negotiations.titlePlaceholder')"
            >
            <p class="form-hint">
              {{ t('negotiations.titleHint') }}
            </p>
          </div>
          <div class="form-field">
            <label
              class="form-label"
              for="n-instruction"
            >{{ t('negotiations.instruction') }}</label>
            <textarea
              id="n-instruction"
              v-model="form.user_instruction"
              class="form-textarea"
              rows="3"
              :placeholder="t('negotiations.instructionPlaceholder')"
            />
            <p class="form-hint">
              {{ t('negotiations.instructionHint') }}
            </p>
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
                  disabled
                  value=""
                >
                  {{ t('negotiations.selectUserAgent') }}
                </option>
                <option
                  v-for="a in userAgents"
                  :key="a.id"
                  :value="a.id"
                >
                  {{ a.name }}
                </option>
              </select>
              <p class="form-hint">
                {{ t('negotiations.userAgentHint') }}
              </p>
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
                  disabled
                  value=""
                >
                  {{ t('negotiations.selectExternalAgent') }}
                </option>
                <option
                  v-for="a in externalAgents"
                  :key="a.id"
                  :value="a.id"
                >
                  {{ a.name }}
                </option>
              </select>
              <p class="form-hint">
                {{ t('negotiations.externalAgentHint') }}
              </p>
            </div>
          </div>
          <div class="form-row form-row--2">
            <div class="form-field">
              <label
                class="form-label"
                for="n-const"
              >{{ t('negotiations.ruleset') }}</label>
              <select
                id="n-const"
                v-model="form.constitution_id"
                class="form-select"
                required
              >
                <option
                  disabled
                  value=""
                >
                  {{ t('negotiations.selectRuleset') }}
                </option>
                <option
                  v-for="c in constitutions"
                  :key="c.id"
                  :value="c.id"
                >
                  {{ c.name }}
                </option>
              </select>
              <p class="form-hint">
                {{ t('negotiations.rulesetHint') }}
              </p>
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
              <p class="form-hint">
                {{ t('negotiations.maxRoundsHint') }}
              </p>
            </div>
          </div>
          <button
            class="btn btn--primary"
            type="submit"
            :disabled="loading || !userAgents.length"
          >
            {{ loading ? t('common.saving') : t('negotiations.createSubmit') }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
