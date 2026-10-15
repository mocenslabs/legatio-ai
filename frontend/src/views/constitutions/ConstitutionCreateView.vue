<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as agentsApi from '@/api/agents'
import * as constitutionsApi from '@/api/constitutions'
import type { RuleInputPayload } from '@/api/constitutions'
import type { Agent } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'

const { t } = useI18n()
const router = useRouter()

interface RuleFormRow {
  key: string
  template: 'approval_amount' | 'deny_amount' | 'deny_privacy' | 'custom'
  name: string
  field: string
  operator: string
  value: string
  action: string
  category: string
  priority: number
}

const agents = ref<Agent[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const successHint = ref<string | null>(null)

const form = reactive({
  name: '',
  description: '',
  agent_id: '',
})

const rules = ref<RuleFormRow[]>([])

function applyTemplate(row: RuleFormRow): void {
  if (row.template === 'approval_amount') {
    row.name = t('constitutions.tplApprovalName')
    row.field = 'amount'
    row.operator = 'GREATER_THAN'
    row.action = 'REQUIRE_APPROVAL'
    row.category = 'BUDGET'
    row.priority = 10
    if (!row.value) row.value = '200'
  } else if (row.template === 'deny_amount') {
    row.name = t('constitutions.tplDenyAmountName')
    row.field = 'amount'
    row.operator = 'GREATER_THAN'
    row.action = 'DENY'
    row.category = 'BUDGET'
    row.priority = 5
    if (!row.value) row.value = '5000'
  } else if (row.template === 'deny_privacy') {
    row.name = t('constitutions.tplDenyPrivacyName')
    row.field = 'shares_phone'
    row.operator = 'EQUALS'
    row.value = 'true'
    row.action = 'DENY'
    row.category = 'PRIVACY'
    row.priority = 1
  }
}

function addRule(template: RuleFormRow['template'] = 'approval_amount'): void {
  const row: RuleFormRow = {
    key: crypto.randomUUID(),
    template,
    name: '',
    field: 'amount',
    operator: 'GREATER_THAN',
    value: template === 'deny_amount' ? '5000' : '200',
    action: 'REQUIRE_APPROVAL',
    category: 'BUDGET',
    priority: 10 + rules.value.length,
  }
  applyTemplate(row)
  rules.value.push(row)
}

function removeRule(key: string): void {
  if (rules.value.length <= 1) return
  rules.value = rules.value.filter((r) => r.key !== key)
}

const livePreview = computed(() => {
  const approval = rules.value.find((r) => r.action === 'REQUIRE_APPROVAL' && r.field === 'amount')
  const deny = rules.value.find((r) => r.action === 'DENY' && r.field === 'amount')
  const parts: string[] = []
  if (approval) {
    parts.push(t('constitutions.previewApproval', { x: approval.value || '…' }))
  }
  if (deny) {
    parts.push(t('constitutions.previewDeny', { x: deny.value || '…' }))
  }
  if (!parts.length) return t('constitutions.previewDefault')
  return parts.join(' ')
})

function parseValue(raw: string, field: string): unknown {
  const s = raw.trim()
  if (field === 'shares_phone' || s === 'true' || s === 'false') return s === 'true'
  const n = Number(s)
  if (!Number.isNaN(n) && s !== '') return n
  return s
}

function toPayload(): RuleInputPayload[] {
  return rules.value.map((r, i) => ({
    rule_number: i + 1,
    name: r.name.trim() || `Rule ${i + 1}`,
    category: r.category,
    field: r.field.trim(),
    operator: r.operator,
    value: parseValue(r.value, r.field),
    action: r.action,
    priority: r.priority || (i + 1) * 10,
  }))
}

async function loadAgents(): Promise<void> {
  try {
    agents.value = await agentsApi.listAgents()
    if (agents.value.length) form.agent_id = agents.value[0].id
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  }
}

async function onSubmit(): Promise<void> {
  error.value = null
  successHint.value = null
  if (!form.name.trim() || !form.agent_id) {
    error.value = t('constitutions.formRequired')
    return
  }
  if (!rules.value.length) {
    error.value = t('constitutions.rulesRequired')
    return
  }
  loading.value = true
  try {
    const res = await constitutionsApi.createConstitutionWithRules({
      agent_id: form.agent_id,
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      rules: toPayload(),
    })
    const cid = res.constitution.id
    const versionId = res.version?.id
    if (versionId) {
      try {
        await constitutionsApi.activateConstitution(cid, versionId)
        successHint.value = t('constitutions.savedActivated')
      } catch {
        /* detail can activate */
      }
    }
    await router.replace({ name: 'constitution-detail', params: { id: cid } })
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  addRule('approval_amount')
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

    <form
      class="stack"
      @submit.prevent="onSubmit"
    >
      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('constitutions.metaTitle') }}
        </div>
        <div class="card-panel__body stack">
          <p class="page-header__subtitle">
            {{ t('constitutions.createFlowHint') }}
          </p>
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
              rows="2"
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
                {{ a.name }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('constitutions.rulesTitle') }}
          <span class="badge badge--brand">{{ rules.length }}</span>
        </div>
        <div class="card-panel__body stack">
          <p class="page-header__subtitle">
            {{ t('constitutions.rulesBuilderHint') }}
          </p>

          <div
            class="rule-preview"
            role="status"
          >
            {{ livePreview }}
          </div>

          <div
            class="page-header__actions"
            style="justify-content: flex-start; flex-wrap: wrap"
          >
            <button
              type="button"
              class="btn btn--secondary btn--sm"
              @click="addRule('approval_amount')"
            >
              + {{ t('constitutions.tplApproval') }}
            </button>
            <button
              type="button"
              class="btn btn--secondary btn--sm"
              @click="addRule('deny_amount')"
            >
              + {{ t('constitutions.tplDenyAmount') }}
            </button>
            <button
              type="button"
              class="btn btn--secondary btn--sm"
              @click="addRule('deny_privacy')"
            >
              + {{ t('constitutions.tplDenyPrivacy') }}
            </button>
          </div>

          <div
            v-for="(row, idx) in rules"
            :key="row.key"
            class="card-panel"
            style="box-shadow: none"
          >
            <div class="card-panel__body stack">
              <div class="form-row form-row--2">
                <div class="form-field">
                  <label class="form-label">{{ t('constitutions.ruleTemplate') }}</label>
                  <select
                    v-model="row.template"
                    class="form-select"
                    @change="applyTemplate(row)"
                  >
                    <option value="approval_amount">
                      {{ t('constitutions.tplApproval') }}
                    </option>
                    <option value="deny_amount">
                      {{ t('constitutions.tplDenyAmount') }}
                    </option>
                    <option value="deny_privacy">
                      {{ t('constitutions.tplDenyPrivacy') }}
                    </option>
                    <option value="custom">
                      {{ t('constitutions.tplCustom') }}
                    </option>
                  </select>
                </div>
                <div class="form-field">
                  <label class="form-label">{{ t('constitutions.ruleValue') }}</label>
                  <input
                    v-model="row.value"
                    class="form-input"
                    required
                  >
                </div>
              </div>

              <details v-if="row.template === 'custom'">
                <summary>{{ t('constitutions.advanced') }}</summary>
                <div
                  class="stack"
                  style="margin-top: 0.75rem"
                >
                  <div class="form-field">
                    <label class="form-label">{{ t('constitutions.ruleName') }}</label>
                    <input
                      v-model="row.name"
                      class="form-input"
                    >
                  </div>
                  <div class="form-row form-row--2">
                    <div class="form-field">
                      <label class="form-label">{{ t('constitutions.ruleField') }}</label>
                      <input
                        v-model="row.field"
                        class="form-input"
                      >
                    </div>
                    <div class="form-field">
                      <label class="form-label">{{ t('constitutions.ruleOperator') }}</label>
                      <select
                        v-model="row.operator"
                        class="form-select"
                      >
                        <option value="GREATER_THAN">
                          GREATER_THAN
                        </option>
                        <option value="EQUALS">
                          EQUALS
                        </option>
                        <option value="LESS_THAN">
                          LESS_THAN
                        </option>
                      </select>
                    </div>
                  </div>
                  <div class="form-field">
                    <label class="form-label">{{ t('constitutions.ruleAction') }}</label>
                    <select
                      v-model="row.action"
                      class="form-select"
                    >
                      <option value="REQUIRE_APPROVAL">
                        REQUIRE_APPROVAL
                      </option>
                      <option value="DENY">
                        DENY
                      </option>
                      <option value="ALLOW">
                        ALLOW
                      </option>
                    </select>
                  </div>
                </div>
              </details>

              <div
                class="page-header__actions"
                style="justify-content: space-between"
              >
                <span class="page-header__subtitle">#{{ idx + 1 }} · {{ row.name }}</span>
                <button
                  type="button"
                  class="btn btn--ghost btn--sm"
                  :disabled="rules.length <= 1"
                  @click="removeRule(row.key)"
                >
                  {{ t('common.delete') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <button
        class="btn btn--primary"
        type="submit"
        :disabled="loading"
      >
        {{ loading ? t('common.saving') : t('constitutions.saveAndActivate') }}
      </button>
    </form>
  </div>
</template>
