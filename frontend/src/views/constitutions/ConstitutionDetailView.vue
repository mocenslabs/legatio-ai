<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import * as constitutionsApi from '@/api/constitutions'
import type { ConstitutionVersion, PolicyRuleRow } from '@/api/constitutions'
import type { Constitution } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass } from '@/utils/format'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const id = computed(() => String(route.params.id || ''))

const item = ref<Constitution | null>(null)
const versions = ref<ConstitutionVersion[]>([])
const rules = ref<PolicyRuleRow[]>([])
const loading = ref(true)
const activating = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const showReplaceDialog = ref(false)

const isDraft = computed(() => String(item.value?.status || '').toUpperCase() === 'DRAFT')
const isActive = computed(() => String(item.value?.status || '').toUpperCase() === 'ACTIVE')

function resolveActiveVersionId(): string | null {
  const av = item.value?.active_version as unknown
  if (typeof av === 'string' && av.length > 0) return av
  if (av && typeof av === 'object' && av !== null && 'id' in av) {
    const oid = (av as { id?: string }).id
    if (oid) return oid
  }
  return null
}

const versionIdToActivate = computed(() => {
  const activeId = resolveActiveVersionId()
  if (activeId) return activeId
  if (!versions.value.length) return null
  const sorted = [...versions.value].sort(
    (a, b) => (b.version_number ?? 0) - (a.version_number ?? 0),
  )
  const draft = sorted.find((v) => String(v.status || '').toUpperCase() === 'DRAFT')
  return (draft || sorted[0])?.id ?? null
})

const displayVersionNumber = computed(() => {
  const n = (item.value as Constitution & { active_version_number?: number })
    ?.active_version_number
  if (n != null) return n
  const activeId = resolveActiveVersionId()
  const v = versions.value.find((x) => x.id === activeId)
  return v?.version_number ?? versions.value[0]?.version_number ?? null
})

function pickRulesFromVersions(): PolicyRuleRow[] {
  const activeId = resolveActiveVersionId()
  const preferred =
    activeId ||
    [...versions.value].sort((a, b) => (b.version_number ?? 0) - (a.version_number ?? 0))[0]
      ?.id ||
    null

  if (!preferred) return []

  const v = versions.value.find((x) => x.id === preferred)
  if (!v) return []

  if (Array.isArray(v.rules) && v.rules.length > 0) return v.rules
  if (Array.isArray(v.rules_snapshot) && v.rules_snapshot.length > 0) return v.rules_snapshot
  return []
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  success.value = null
  try {
    item.value = await constitutionsApi.getConstitution(id.value)
    versions.value = await constitutionsApi.listVersions(id.value).catch(() => [])
    rules.value = pickRulesFromVersions()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
    item.value = null
    rules.value = []
  } finally {
    loading.value = false
  }
}

async function doActivate(replaceActive: boolean): Promise<void> {
  if (!versionIdToActivate.value) {
    error.value = t('constitutions.activateNoVersion')
    return
  }
  activating.value = true
  error.value = null
  success.value = null
  try {
    const res = await constitutionsApi.activateConstitution(
      id.value,
      versionIdToActivate.value,
      { replaceActive },
    )
    item.value = res.constitution
    versions.value = await constitutionsApi.listVersions(id.value).catch(() => versions.value)
    rules.value = pickRulesFromVersions()
    showReplaceDialog.value = false
    success.value = replaceActive
      ? t('constitutions.activateReplaced')
      : t('constitutions.activateSuccess')
  } catch (err) {
    if (!replaceActive && constitutionsApi.isActiveConflictError(err)) {
      showReplaceDialog.value = true
      error.value = null
    } else {
      error.value = extractApiMessage(err, t('constitutions.activateFailed'))
    }
  } finally {
    activating.value = false
  }
}

async function onActivate(): Promise<void> {
  await doActivate(false)
}

function onConfirmReplace(): void {
  void doActivate(true)
}

function onCancelReplace(): void {
  showReplaceDialog.value = false
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
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
          {{ item?.name || t('constitutions.detailTitle') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('constitutions.subtitle') }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          @click="router.push({ name: 'constitutions' })"
        >
          {{ t('common.back') }}
        </button>
        <button
          v-if="isDraft"
          type="button"
          class="btn btn--primary btn--sm"
          :disabled="activating || loading || !versionIdToActivate"
          @click="onActivate"
        >
          {{ activating ? t('common.saving') : t('constitutions.activate') }}
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
    <div
      v-if="success"
      class="form-alert form-alert--success"
      role="status"
    >
      {{ success }}
    </div>
    <div
      v-if="isDraft && !versionIdToActivate && !loading"
      class="form-alert"
      role="status"
    >
      {{ t('constitutions.activateNoVersion') }}
    </div>
    <div
      v-if="loading"
      class="loading-block"
    >
      {{ t('common.loading') }}
    </div>

    <div
      v-else-if="item"
      class="stack"
    >
      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('constitutions.metaTitle') }}
        </div>
        <div class="card-panel__body meta-grid">
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('constitutions.colStatus') }}
            </div>
            <div class="meta-item__value">
              <span :class="statusBadgeClass(item.status)">{{ item.status }}</span>
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('constitutions.version') }}
            </div>
            <div class="meta-item__value">
              v{{ displayVersionNumber ?? '—' }}
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('constitutions.colUpdated') }}
            </div>
            <div class="meta-item__value">
              {{ formatDate(item.updated_at || item.created_at) }}
            </div>
          </div>
        </div>
        <div
          v-if="isDraft"
          class="card-panel__body"
        >
          <p class="page-header__subtitle">
            {{ t('constitutions.activateHint') }}
          </p>
        </div>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('constitutions.rulesTitle') }}
          <span class="badge badge--brand">{{ rules.length }}</span>
        </div>
        <div class="card-panel__body">
          <div
            v-if="rules.length === 0"
            class="empty-state"
          >
            <strong>{{ t('constitutions.noRules') }}</strong>
            <p class="page-header__subtitle">
              {{ t('constitutions.noRulesHint') }}
            </p>
          </div>
          <div
            v-else
            class="rule-list"
          >
            <div
              v-for="rule in rules"
              :key="rule.id || String(rule.rule_number) + rule.name"
              class="rule-item"
            >
              <div class="rule-item__num">
                #{{ rule.rule_number ?? '—' }}
              </div>
              <div>
                <div class="rule-item__name">
                  {{ rule.name }}
                </div>
                <div class="rule-item__meta">
                  {{ rule.category }} · {{ rule.field }} {{ rule.operator }}
                  {{ formatValue(rule.value) }}
                </div>
              </div>
              <span :class="statusBadgeClass(rule.action)">{{ rule.action }}</span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="isActive"
        class="next-step"
      >
        <p>
          {{ t('constitutions.nextNegotiation') }}
        </p>
        <button
          type="button"
          class="btn btn--primary btn--sm"
          @click="router.push({ name: 'negotiation-create' })"
        >
          {{ t('negotiations.create') }}
        </button>
      </div>
    </div>

    <!-- Replace active constitution dialog -->
    <div
      v-if="showReplaceDialog"
      class="modal-backdrop"
      role="presentation"
      @click.self="onCancelReplace"
    >
      <div
        class="modal-panel"
        role="dialog"
        aria-modal="true"
        :aria-label="t('constitutions.replaceTitle')"
      >
        <h2 class="modal-panel__title">
          {{ t('constitutions.replaceTitle') }}
        </h2>
        <p class="modal-panel__body">
          {{ t('constitutions.replaceBody') }}
        </p>
        <div class="modal-panel__actions">
          <button
            type="button"
            class="btn btn--secondary btn--sm"
            :disabled="activating"
            @click="onCancelReplace"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="button"
            class="btn btn--primary btn--sm"
            :disabled="activating"
            @click="onConfirmReplace"
          >
            {{ activating ? t('common.saving') : t('constitutions.replaceConfirm') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.55);
}

.modal-panel {
  width: min(28rem, 100%);
  padding: 1.25rem 1.35rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: var(--color-surface, #12181f);
  color: inherit;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

.modal-panel__title {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
}

.modal-panel__body {
  margin: 0 0 1.1rem;
  font-size: 0.95rem;
  line-height: 1.45;
  opacity: 0.9;
}

.modal-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

@media (max-width: 480px) {
  .modal-panel__actions {
    flex-direction: column-reverse;
  }

  .modal-panel__actions .btn {
    width: 100%;
  }
}
</style>
