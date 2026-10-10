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
const actingId = ref<string | null>(null)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

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
    await approvalsApi.approveRequest(id, 'Approved from UI')
    success.value = t('approvals.approved')
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
    await approvalsApi.rejectRequest(id, 'Rejected from UI')
    success.value = t('approvals.rejected')
    await load()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    actingId.value = null
  }
}

function labelStatus(status?: string): string {
  const key = statusLabelKey(status)
  if (key === 'status.raw') return status || '—'
  return t(key)
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
      v-else
      class="card-panel"
    >
      <div
        v-if="items.length === 0"
        class="empty-state"
      >
        <strong>{{ t('approvals.emptyTitle') }}</strong>
        <p>{{ t('approvals.emptyBody') }}</p>
        <div class="empty-state__actions">
          <button
            type="button"
            class="btn btn--secondary"
            @click="router.push({ name: 'negotiations' })"
          >
            {{ t('nav.negotiations') }}
          </button>
        </div>
      </div>
      <div
        v-else
        class="data-table-wrap"
      >
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('approvals.colSummary') }}</th>
              <th>{{ t('approvals.colStatus') }}</th>
              <th>{{ t('approvals.colExpires') }}</th>
              <th>{{ t('approvals.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="a in items"
              :key="a.id"
            >
              <td>{{ a.summary || a.id.slice(0, 8) }}</td>
              <td>
                <span :class="statusBadgeClass(a.status)">{{ labelStatus(a.status) }}</span>
              </td>
              <td>{{ formatDate(a.expires_at) }}</td>
              <td>
                <div class="page-header__actions">
                  <button
                    type="button"
                    class="btn btn--primary btn--sm"
                    :disabled="actingId === a.id"
                    @click="onApprove(a.id)"
                  >
                    {{ t('approvals.approve') }}
                  </button>
                  <button
                    type="button"
                    class="btn btn--danger btn--sm"
                    :disabled="actingId === a.id"
                    @click="onReject(a.id)"
                  >
                    {{ t('approvals.reject') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
