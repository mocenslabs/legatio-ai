<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as agentsApi from '@/api/agents'
import type { Agent } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass, statusLabelKey } from '@/utils/format'

const { t } = useI18n()
const router = useRouter()

const items = ref<Agent[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const mine = computed(() =>
  items.value.filter((a) => String(a.agent_type).toUpperCase().includes('USER')),
)
const others = computed(() =>
  items.value.filter((a) => !String(a.agent_type).toUpperCase().includes('USER')),
)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await agentsApi.listAgents()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

async function onDelete(id: string): Promise<void> {
  if (!confirm(t('agents.confirmDelete'))) return
  try {
    await agentsApi.deleteAgent(id)
    await load()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
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
          {{ t('agents.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('agents.subtitle') }}
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
          @click="router.push({ name: 'agent-create' })"
        >
          {{ t('agents.create') }}
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
      class="stack"
    >
      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('agents.mineTitle') }}
          <span class="badge badge--brand">{{ mine.length }}</span>
        </div>
        <div class="card-panel__body">
          <div
            v-if="mine.length === 0"
            class="empty-state"
          >
            <strong>{{ t('agents.emptyMine') }}</strong>
            <p>{{ t('agents.emptyMineBody') }}</p>
            <div class="empty-state__actions">
              <button
                type="button"
                class="btn btn--primary"
                @click="router.push({ name: 'agent-create' })"
              >
                {{ t('agents.create') }}
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
                  <th>{{ t('agents.colName') }}</th>
                  <th>{{ t('agents.colType') }}</th>
                  <th>{{ t('agents.colStatus') }}</th>
                  <th>{{ t('agents.colUpdated') }}</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="a in mine"
                  :key="a.id"
                >
                  <td>{{ a.name }}</td>
                  <td>{{ a.agent_type }}</td>
                  <td>
                    <span :class="statusBadgeClass(a.status)">{{ labelStatus(a.status) }}</span>
                  </td>
                  <td>{{ formatDate(a.updated_at || a.created_at) }}</td>
                  <td>
                    <button
                      type="button"
                      class="btn btn--ghost btn--sm"
                      @click="onDelete(a.id)"
                    >
                      {{ t('common.delete') }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="next-step">
              <p>{{ t('agents.nextConstitution') }}</p>
              <button
                type="button"
                class="btn btn--primary btn--sm"
                @click="router.push({ name: 'constitution-create' })"
              >
                {{ t('constitutions.create') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('agents.externalTitle') }}
          <span class="badge badge--neutral">{{ others.length }}</span>
        </div>
        <div class="card-panel__body">
          <p class="page-header__subtitle">
            {{ t('agents.externalHint') }}
          </p>
          <div
            v-if="others.length === 0"
            class="empty-state"
          >
            <strong>{{ t('agents.emptyExternal') }}</strong>
            <p>{{ t('agents.emptyExternalBody') }}</p>
          </div>
          <div
            v-else
            class="data-table-wrap"
          >
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ t('agents.colName') }}</th>
                  <th>{{ t('agents.colType') }}</th>
                  <th>{{ t('agents.colStatus') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="a in others"
                  :key="a.id"
                >
                  <td>{{ a.name }}</td>
                  <td>{{ a.agent_type }}</td>
                  <td>
                    <span :class="statusBadgeClass(a.status)">{{ labelStatus(a.status) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
