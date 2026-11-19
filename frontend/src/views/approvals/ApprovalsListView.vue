<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as approvalsApi from '@/api/approvals'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ApprovalRequest } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass, statusLabelKey } from '@/utils/format'

const { t } = useI18n()
const router = useRouter()

const items = ref<ApprovalRequest[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const actingId = ref<string | null>(null)
const success = ref<string | null>(null)

function labelStatus(status?: string): string {
  const key = statusLabelKey(status)
  if (key === 'status.raw') return status || '—'
  return t(key)
}

function labelRisk(level?: string): string {
  if (!level) return '—'
  const u = String(level).toUpperCase()
  if (u === 'LOW') return t('approvals.riskLow')
  if (u === 'MEDIUM' || u === 'MED') return t('approvals.riskMedium')
  if (u === 'HIGH') return t('approvals.riskHigh')
  if (u === 'CRITICAL') return t('approvals.riskCritical')
  return level
}

function amountLabel(item: ApprovalRequest): string {
  if (item.proposal_amount != null && item.proposal_amount !== '') {
    return String(item.proposal_amount)
  }
  if (item.proposal?.amount != null) {
    const cur = item.proposal.currency ? ` ${item.proposal.currency}` : ''
    return `${item.proposal.amount}${cur}`
  }
  return '—'
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await approvalsApi.listPendingApprovals()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

async function onApprove(id: string): Promise<void> {
  actingId.value = id
  error.value = null
  success.value = null
  try {
    await approvalsApi.approveRequest(id)
    success.value = t('approvals.approvedOk')
    await load()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    actingId.value = null
  }
}

async function onReject(id: string): Promise<void> {
  actingId.value = id
  error.value = null
  success.value = null
  try {
    await approvalsApi.rejectRequest(id)
    success.value = t('approvals.rejectedOk')
    await load()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    actingId.value = null
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
          {{ t('approvals.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('approvals.subtitle') }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          :disabled="loading"
          @click="load"
        >
          {{ t('common.refresh') }}
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
      v-if="loading"
      class="loading-block"
    >
      {{ t('common.loading') }}
    </div>

    <div
      v-else-if="items.length === 0"
      class="card-panel"
    >
      <div class="card-panel__body">
        <EmptyState
          :title="t('approvals.emptyTitle')"
          :body="t('approvals.emptyBody')"
        >
          <template #actions>
            <button
              type="button"
              class="btn btn--secondary btn--sm"
              @click="router.push({ name: 'negotiations' })"
            >
              {{ t('approvals.emptyCta') }}
            </button>
            <button
              type="button"
              class="btn btn--secondary btn--sm"
              @click="router.push({ name: 'help' })"
            >
              {{ t('nav.help') }}
            </button>
          </template>
        </EmptyState>
      </div>
    </div>

    <div
      v-else
      class="stack"
    >
      <div class="rules-explainer">
        <p class="rules-explainer__title">
          {{ t('approvals.explainerTitle') }}
        </p>
        <ol class="rules-explainer__list">
          <li>{{ t('approvals.explainer1') }}</li>
          <li>{{ t('approvals.explainer2') }}</li>
          <li>{{ t('approvals.explainer3') }}</li>
        </ol>
      </div>

      <div
        v-for="item in items"
        :key="item.id"
        class="card-panel"
      >
        <div class="card-panel__body stack">
          <div class="meta-grid">
            <div class="meta-item">
              <div class="meta-item__label">
                {{ t('approvals.colAmount') }}
              </div>
              <div class="meta-item__value">
                {{ amountLabel(item) }}
              </div>
            </div>
            <div class="meta-item">
              <div class="meta-item__label">
                {{ t('approvals.colActionType') }}
              </div>
              <div class="meta-item__value">
                {{ item.proposal_action_type || item.proposal?.action_type || '—' }}
              </div>
            </div>
            <div class="meta-item">
              <div class="meta-item__label">
                {{ t('approvals.colRisk') }}
              </div>
              <div class="meta-item__value">
                {{ labelRisk(item.risk_level) }}
              </div>
            </div>
            <div class="meta-item">
              <div class="meta-item__label">
                {{ t('approvals.colStatus') }}
              </div>
              <div class="meta-item__value">
                <span :class="statusBadgeClass(item.status)">{{ labelStatus(item.status) }}</span>
                <span
                  v-if="item.is_expired"
                  class="badge badge--danger"
                >{{ t('approvals.expired') }}</span>
              </div>
            </div>
            <div class="meta-item">
              <div class="meta-item__label">
                {{ t('approvals.colCreated') }}
              </div>
              <div class="meta-item__value">
                {{ formatDate(item.created_at) }}
              </div>
            </div>
            <div class="meta-item">
              <div class="meta-item__label">
                {{ t('approvals.colExpires') }}
              </div>
              <div class="meta-item__value">
                {{ item.expires_at ? formatDate(item.expires_at) : '—' }}
              </div>
            </div>
          </div>

          <div class="rule-preview">
            <strong>{{ t('approvals.colReason') }}</strong>
            <pre class="form-hint approval-summary">{{ item.summary || t('approvals.noSummary') }}</pre>
          </div>

          <p class="form-hint">
            {{ t('approvals.decideHint') }}
          </p>
          <div class="page-header__actions">
            <button
              type="button"
              class="btn btn--primary btn--sm"
              :disabled="actingId === item.id || item.is_expired"
              @click="onApprove(item.id)"
            >
              {{ t('approvals.approve') }}
            </button>
            <button
              type="button"
              class="btn btn--secondary btn--sm"
              :disabled="actingId === item.id"
              @click="onReject(item.id)"
            >
              {{ t('approvals.reject') }}
            </button>
            <button
              type="button"
              class="btn btn--ghost btn--sm"
              @click="router.push({ name: 'negotiations' })"
            >
              {{ t('approvals.backNegotiations') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
