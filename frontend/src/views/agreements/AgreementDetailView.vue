<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import * as agreementsApi from '@/api/agreements'
import type { Agreement } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass } from '@/utils/format'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const item = ref<Agreement | null>(null)
const canonical = ref<Record<string, unknown> | null>(null)
const loading = ref(true)
const acting = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const canSign = computed(() => {
  const s = item.value?.status?.toUpperCase()
  return s === 'DRAFT' || (item.value && !item.value.is_signed && s !== 'SIGNED' && s !== 'EXECUTED')
})

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const id = String(route.params.id)
    item.value = await agreementsApi.getAgreement(id)
    try {
      canonical.value = await agreementsApi.getCanonical(id)
    } catch {
      canonical.value = null
    }
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    loading.value = false
  }
}

async function onSign(): Promise<void> {
  if (!item.value) return
  acting.value = true
  error.value = null
  success.value = null
  try {
    await agreementsApi.signAgreement(item.value.id)
    success.value = t('agreements.signed')
    await load()
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    acting.value = false
  }
}

async function onVerify(): Promise<void> {
  if (!item.value) return
  acting.value = true
  error.value = null
  success.value = null
  try {
    const res = await agreementsApi.verifyAgreement(item.value.id)
    success.value = t('agreements.verified', { result: JSON.stringify(res) })
  } catch (err) {
    error.value = extractApiMessage(err, t('errors.unknown'))
  } finally {
    acting.value = false
  }
}

async function onExport(): Promise<void> {
  if (!item.value) return
  acting.value = true
  error.value = null
  try {
    const blob = await agreementsApi.exportAgreement(item.value.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `agreement_${item.value.reference_code || item.value.id}.json`
    a.click()
    URL.revokeObjectURL(url)
    success.value = t('agreements.exported')
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
          {{ item?.reference_code || t('agreements.detailTitle') }}
        </h1>
        <p class="page-header__subtitle">
          {{ item?.room_reference_code || '' }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          @click="router.push({ name: 'agreements' })"
        >
          {{ t('common.back') }}
        </button>
        <button
          v-if="canSign"
          type="button"
          class="btn btn--primary btn--sm"
          :disabled="acting"
          @click="onSign"
        >
          {{ t('agreements.sign') }}
        </button>
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          :disabled="acting"
          @click="onVerify"
        >
          {{ t('agreements.verify') }}
        </button>
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          :disabled="acting"
          @click="onExport"
        >
          {{ t('agreements.export') }}
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
      v-else-if="item"
      class="stack"
    >
      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('agreements.metaTitle') }}
        </div>
        <div class="card-panel__body meta-grid">
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('agreements.colStatus') }}
            </div>
            <div class="meta-item__value">
              <span :class="statusBadgeClass(item.status)">{{ item.status }}</span>
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('agreements.colAmount') }}
            </div>
            <div class="meta-item__value">
              {{ item.proposal_amount ?? '—' }}
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('agreements.colSigned') }}
            </div>
            <div class="meta-item__value">
              {{ formatDate(item.signed_at) }}
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              Hash
            </div>
            <div class="meta-item__value">
              {{ item.canonical_hash || '—' }}
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="canonical"
        class="card-panel"
      >
        <div class="card-panel__header">
          {{ t('agreements.canonical') }}
        </div>
        <div class="card-panel__body">
          <pre class="meta-item__value">{{ JSON.stringify(canonical, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
