<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import * as auditApi from '@/api/audit'
import type { AuditEvent } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate } from '@/utils/format'

const { t } = useI18n()
const items = ref<AuditEvent[]>([])
const loading = ref(true)
const acting = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await auditApi.listAuditEvents()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

async function onVerify(): Promise<void> {
  acting.value = true
  error.value = null
  success.value = null
  try {
    const res = await auditApi.verifyAuditChain()
    success.value = t('audit.verified', { result: JSON.stringify(res) })
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    acting.value = false
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
          {{ t('audit.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('audit.subtitle') }}
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
        <button
          type="button"
          class="btn btn--primary btn--sm"
          :disabled="acting"
          @click="onVerify"
        >
          {{ t('audit.verifyChain') }}
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
        <strong>{{ t('audit.emptyTitle') }}</strong>
        {{ t('audit.emptyBody') }}
      </div>
      <div
        v-else
        class="data-table-wrap"
      >
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('audit.colType') }}</th>
              <th>{{ t('audit.colEntity') }}</th>
              <th>{{ t('audit.colActor') }}</th>
              <th>{{ t('audit.colWhen') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="e in items"
              :key="e.id"
            >
              <td>{{ e.event_type }}</td>
              <td>{{ e.entity_type }} {{ e.entity_id ? String(e.entity_id).slice(0, 8) : '' }}</td>
              <td>{{ e.actor_type || '—' }}</td>
              <td>{{ formatDate(e.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
