<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import * as negotiationsApi from '@/api/negotiations'
import type { NegotiationRoom, Proposal } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass } from '@/utils/format'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const room = ref<NegotiationRoom | null>(null)
const proposals = ref<Proposal[]>([])
const lastOutcome = ref<string | null>(null)
const loading = ref(true)
const acting = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const canStart = computed(() => room.value?.status === 'PENDING')
const canProcess = computed(() =>
  ['IN_PROGRESS', 'AWAITING_APPROVAL'].includes(room.value?.status || ''),
)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const id = String(route.params.id)
    room.value = await negotiationsApi.getNegotiation(id)
    try {
      proposals.value = await negotiationsApi.listProposals(id)
    } catch {
      proposals.value = []
    }
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

async function onStart(): Promise<void> {
  if (!room.value) return
  acting.value = true
  error.value = null
  success.value = null
  try {
    room.value = await negotiationsApi.startNegotiation(room.value.id)
    success.value = t('negotiations.started')
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    acting.value = false
  }
}

async function onProcessRound(): Promise<void> {
  if (!room.value) return
  acting.value = true
  error.value = null
  success.value = null
  try {
    const result = await negotiationsApi.processRound(room.value.id)
    room.value = result.room
    lastOutcome.value = result.round_result?.outcome ?? null
    success.value = t('negotiations.roundProcessed', {
      outcome: lastOutcome.value || '—',
    })
    try {
      proposals.value = await negotiationsApi.listProposals(room.value.id)
    } catch {
      /* ignore */
    }
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
          {{ room?.title || t('negotiations.detailTitle') }}
        </h1>
        <p class="page-header__subtitle">
          {{ room?.reference_code || '' }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          @click="router.push({ name: 'negotiations' })"
        >
          {{ t('common.back') }}
        </button>
        <button
          v-if="canStart"
          type="button"
          class="btn btn--primary btn--sm"
          :disabled="acting"
          @click="onStart"
        >
          {{ t('negotiations.start') }}
        </button>
        <button
          v-if="canProcess"
          type="button"
          class="btn btn--primary btn--sm"
          :disabled="acting"
          @click="onProcessRound"
        >
          {{ t('negotiations.processRound') }}
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
      v-else-if="room"
      class="stack"
    >
      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('negotiations.metaTitle') }}
        </div>
        <div class="card-panel__body meta-grid">
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('negotiations.colStatus') }}
            </div>
            <div class="meta-item__value">
              <span :class="statusBadgeClass(room.status)">{{ room.status }}</span>
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('negotiations.colRound') }}
            </div>
            <div class="meta-item__value">
              {{ room.current_round ?? 0 }}/{{ room.max_rounds ?? '—' }}
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('negotiations.instruction') }}
            </div>
            <div class="meta-item__value">
              {{ room.user_instruction || '—' }}
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('negotiations.colUpdated') }}
            </div>
            <div class="meta-item__value">
              {{ formatDate(room.updated_at || room.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('negotiations.proposalsTitle') }}
          <span class="badge badge--brand">{{ proposals.length }}</span>
        </div>
        <div class="card-panel__body">
          <div
            v-if="proposals.length === 0"
            class="empty-state"
          >
            {{ t('negotiations.noProposals') }}
          </div>
          <div
            v-else
            class="data-table-wrap"
          >
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ t('negotiations.colRound') }}</th>
                  <th>{{ t('negotiations.colAmount') }}</th>
                  <th>{{ t('negotiations.colStatus') }}</th>
                  <th>{{ t('negotiations.colType') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="p in proposals"
                  :key="p.id"
                >
                  <td>{{ p.round_number ?? '—' }}</td>
                  <td>
                    <template v-if="p.amount != null">
                      {{ p.amount }} {{ p.currency || '' }}
                    </template>
                    <template v-else>
                      —
                    </template>
                  </td>
                  <td><span :class="statusBadgeClass(p.status)">{{ p.status }}</span></td>
                  <td>{{ p.action_type || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
