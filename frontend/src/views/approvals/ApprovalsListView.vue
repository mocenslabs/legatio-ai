<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as approvalsApi from '@/api/approvals'
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
        <h1 class="page-header__title">{{ t('approvals.title') }}</h1>
        <p class="page-header__subtitle">{{ t('approvals.subtitle') }}</p>
      </div>
    </div>

    <div v-if="error" class="form-alert" role="alert">{{ error }}</div>
    <div v-if="success" class="form-alert form-alert--success" role="status">{{ success }}</div>
    <div v-if="loading" class="loading-block">{{ t('common.loading') }}</div>

    <div v-else-if="items.length === 0" class="card-panel">
      <div class="card-panel__body empty-state">
        <strong>{{ t('approvals.emptyTitle') }}</strong>
        <p class="page-header__subtitle">{{ t('approvals.emptyBody') }}</p>
        <button type="button" class="btn btn--secondary btn--sm" @click="router.push({ name: 'negotiations' })">
          {{ t('approvals.emptyCta') }}
        </button>
      </div>
    </div>

    <div v-else class="stack">
      <div v-for="item in items" :key="item.id" class="card-panel">
        <div class="card-panel__body stack">
          <div class="meta-grid">
            <div class="meta-item">
              <div class="meta-item__label">{{ t('approvals.colStatus') }}</div>
              <div class="meta-item__value">
                <span :class="statusBadgeClass(item.status)">{{ labelStatus(item.status) }}</span>
              </div>
            </div>
            <div class="meta-item">
              <div class="meta-item__label">{{ t('approvals.colCreated') }}</div>
              <div class="meta-item__value">{{ formatDate(item.created_at) }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-item__label">{{ t('approvals.colReason') }}</div>
              <div class="meta-item__value">{{ item.reason || item.summary || '—' }}</div>
            </div>
          </div>
          <p class="page-header__subtitle">{{ t('approvals.decideHint') }}</p>
          <div class="page-header__actions" style="justify-content: flex-start">
            <button
              type="button"
              class="btn btn--primary btn--sm"
              :disabled="actingId === item.id"
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
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
