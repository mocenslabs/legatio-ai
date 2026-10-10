<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as constitutionsApi from '@/api/constitutions'
import type { Constitution } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass, statusLabelKey } from '@/utils/format'

const { t } = useI18n()
const router = useRouter()

const items = ref<Constitution[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await constitutionsApi.listConstitutions()
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
          {{ t('constitutions.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('constitutions.subtitle') }}
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
          @click="router.push({ name: 'constitution-create' })"
        >
          {{ t('constitutions.create') }}
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
        <strong>{{ t('constitutions.emptyTitle') }}</strong>
        <p>{{ t('constitutions.emptyBody') }}</p>
        <div class="empty-state__actions">
          <button
            type="button"
            class="btn btn--primary"
            @click="router.push({ name: 'constitution-create' })"
          >
            {{ t('constitutions.create') }}
          </button>
          <button
            type="button"
            class="btn btn--secondary"
            @click="router.push({ name: 'agents' })"
          >
            {{ t('nav.agents') }}
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
              <th>{{ t('constitutions.colName') }}</th>
              <th>{{ t('constitutions.colStatus') }}</th>
              <th>{{ t('constitutions.colUpdated') }}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in items"
              :key="c.id"
            >
              <td>
                <RouterLink :to="{ name: 'constitution-detail', params: { id: c.id } }">
                  {{ c.name }}
                </RouterLink>
              </td>
              <td>
                <span :class="statusBadgeClass(c.status)">{{ labelStatus(c.status) }}</span>
              </td>
              <td>{{ formatDate(c.updated_at || c.created_at) }}</td>
              <td>
                <RouterLink :to="{ name: 'constitution-detail', params: { id: c.id } }">
                  {{ t('common.view') }}
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="next-step">
          <p>{{ t('constitutions.nextNegotiation') }}</p>
          <button
            type="button"
            class="btn btn--primary btn--sm"
            @click="router.push({ name: 'negotiation-create' })"
          >
            {{ t('negotiations.create') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
