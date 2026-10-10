<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'


import * as agreementsApi from '@/api/agreements'
import type { Agreement } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass } from '@/utils/format'

const { t } = useI18n()

const items = ref<Agreement[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await agreementsApi.listAgreements()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
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
          {{ t('agreements.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('agreements.subtitle') }}
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
        <strong>{{ t('agreements.emptyTitle') }}</strong>
        {{ t('agreements.emptyBody') }}
      </div>
      <div
        v-else
        class="data-table-wrap"
      >
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('agreements.colRef') }}</th>
              <th>{{ t('agreements.colStatus') }}</th>
              <th>{{ t('agreements.colAmount') }}</th>
              <th>{{ t('agreements.colSigned') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="a in items"
              :key="a.id"
            >
              <td>
                <RouterLink :to="{ name: 'agreement-detail', params: { id: a.id } }">
                  {{ a.reference_code || a.id.slice(0, 8) }}
                </RouterLink>
              </td>
              <td><span :class="statusBadgeClass(a.status)">{{ a.status }}</span></td>
              <td>{{ a.proposal_amount ?? '—' }}</td>
              <td>{{ formatDate(a.signed_at || a.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
