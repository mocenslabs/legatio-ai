<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import * as negotiationsApi from '@/api/negotiations'
import type { NegotiationRoom, Proposal } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass, statusLabelKey } from '@/utils/format'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const room = ref<NegotiationRoom | null>(null)
const proposals = ref<Proposal[]>([])
const lastOutcome = ref<string | null>(null)
const lastPolicyReason = ref<string | null>(null)
const lastPolicyOutcome = ref<string | null>(null)
const loading = ref(true)
const acting = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const canStart = computed(() => room.value?.status === 'PENDING')
const isAwaiting = computed(() =>
  ['AWAITING_APPROVAL', 'PENDING_APPROVAL'].includes(String(room.value?.status || '')),
)
const canProcess = computed(() => {
  const s = room.value?.status || ''
  return s === 'IN_PROGRESS' || isAwaiting.value
})

const nextHint = computed(() => {
  if (!room.value) return ''
  if (canStart.value) return t('negotiations.nextStart')
  if (isAwaiting.value) return t('negotiations.nextApproval')
  if (canProcess.value) return t('negotiations.nextRound')
  if (['COMPLETED', 'SIGNED', 'EXECUTED', 'FAILED', 'REJECTED', 'CANCELLED'].includes(String(room.value.status))) {
    return t('negotiations.nextDone')
  }
  return t('negotiations.nextIdle')
})

const lastProposal = computed(() => {
  if (!proposals.value.length) return null
  return [...proposals.value].sort(
    (a, b) => (b.round_number ?? 0) - (a.round_number ?? 0),
  )[0]
})

function labelStatus(status?: string): string {
  const key = statusLabelKey(status)
  if (key === 'status.raw') return status || '—'
  return t(key)
}

function humanOutcome(raw?: string | null): string {
  if (!raw) return '—'
  const u = String(raw).toUpperCase()
  if (u.includes('REQUIRE') || u.includes('APPROVAL')) return t('negotiations.outcomeAsk')
  if (u.includes('DENY') || u.includes('REJECT')) return t('negotiations.outcomeDeny')
  if (u.includes('ALLOW') || u.includes('ACCEPT')) return t('negotiations.outcomeAllow')
  if (u.includes('ERROR')) return t('negotiations.outcomeError')
  return raw
}

function formatDataFields(p: Proposal): string {
  const fields = p.data_fields_requested
  if (!fields || !fields.length) return t('negotiations.noPrivateData')
  return fields.join(', ')
}

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
    await load()
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
    const res = await negotiationsApi.processRound(room.value.id)
    room.value = res.room
    const outcome = res.round_result?.outcome || res.round_result?.policy_decision?.outcome
    lastOutcome.value = outcome || null
    lastPolicyOutcome.value = res.round_result?.policy_decision?.outcome || outcome || null
    lastPolicyReason.value = res.round_result?.policy_decision?.reason || null
    success.value = t('negotiations.roundProcessedHuman', {
      outcome: humanOutcome(outcome),
    })
    try {
      proposals.value = await negotiationsApi.listProposals(room.value.id)
    } catch {
      /* keep previous */
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
          {{ t('negotiations.detailSubtitle') }}
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
          v-if="canProcess && !isAwaiting"
          type="button"
          class="btn btn--primary btn--sm"
          :disabled="acting"
          @click="onProcessRound"
        >
          {{ t('negotiations.processRound') }}
        </button>
        <button
          v-if="isAwaiting"
          type="button"
          class="btn btn--primary btn--sm"
          @click="router.push({ name: 'approvals' })"
        >
          {{ t('negotiations.goApprovals') }}
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
        <div class="card-panel__body stack">
          <div class="rules-explainer">
            <p class="rules-explainer__title">
              {{ t('negotiations.nextLabel') }}
            </p>
            <p
              class="form-hint"
              style="margin: 0"
            >
              {{ nextHint }}
            </p>
            <p
              v-if="lastProposal"
              class="form-hint"
            >
              {{
                t('negotiations.lastProposal', {
                  amount: lastProposal.amount ?? '—',
                  currency: lastProposal.currency || '',
                  status: labelStatus(lastProposal.status),
                })
              }}
            </p>
            <p
              v-if="lastPolicyOutcome"
              class="rules-explainer__priority"
            >
              {{ t('negotiations.lastPolicy', { outcome: humanOutcome(lastPolicyOutcome) }) }}
            </p>
            <p
              v-if="lastPolicyReason"
              class="form-hint"
            >
              {{ lastPolicyReason }}
            </p>
          </div>
        </div>
      </div>

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
              <span :class="statusBadgeClass(room.status)">{{ labelStatus(room.status) }}</span>
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
          <p class="form-hint">
            {{ t('negotiations.proposalsHint') }}
          </p>
          <div
            v-if="proposals.length === 0"
            class="empty-state"
          >
            <strong>{{ t('negotiations.noProposals') }}</strong>
            <p>{{ t('negotiations.noProposalsBody') }}</p>
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
                  <th>{{ t('negotiations.colData') }}</th>
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
                  <td>{{ formatDataFields(p) }}</td>
                  <td>
                    <span :class="statusBadgeClass(p.status)">{{ labelStatus(p.status) }}</span>
                  </td>
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
