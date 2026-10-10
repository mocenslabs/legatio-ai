<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as negotiationsApi from '@/api/negotiations'
import type { NegotiationRoom } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass, statusLabelKey } from '@/utils/format'

const { t } = useI18n()
const router = useRouter()

const items = ref<NegotiationRoom[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await negotiationsApi.listNegotiations()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
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
          {{ t('negotiations.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('negotiations.subtitle') }}
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
          @click="router.push({ name: 'negotiation-create' })"
        >
          {{ t('negotiations.create') }}
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
        <strong>{{ t('negotiations.emptyTitle') }}</strong>
        <p>{{ t('negotiations.emptyBody') }}</p>
        <div class="empty-state__actions">
          <button
            type="button"
            class="btn btn--primary"
            @click="router.push({ name: 'negotiation-create' })"
          >
            {{ t('negotiations.create') }}
          </button>
          <button
            type="button"
            class="btn btn--secondary"
            @click="router.push({ name: 'help' })"
          >
            {{ t('nav.help') }}
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
              <th>{{ t('negotiations.colRef') }}</th>
              <th>{{ t('negotiations.colTitle') }}</th>
              <th>{{ t('negotiations.colStatus') }}</th>
              <th>{{ t('negotiations.colRound') }}</th>
              <th>{{ t('negotiations.colUpdated') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="n in items"
              :key="n.id"
            >
              <td>
                <RouterLink :to="{ name: 'negotiation-detail', params: { id: n.id } }">
                  {{ n.reference_code || n.id.slice(0, 8) }}
                </RouterLink>
              </td>
              <td>{{ n.title }}</td>
              <td>
                <span :class="statusBadgeClass(n.status)">{{ labelStatus(n.status) }}</span>
              </td>
              <td>{{ n.current_round ?? 0 }}/{{ n.max_rounds ?? '—' }}</td>
              <td>{{ formatDate(n.updated_at || n.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
