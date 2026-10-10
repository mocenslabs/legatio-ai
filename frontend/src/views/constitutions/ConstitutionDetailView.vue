<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import * as constitutionsApi from '@/api/constitutions'
import type { Constitution } from '@/types/domain'
import { extractApiMessage } from '@/utils/errors'
import { formatDate, statusBadgeClass } from '@/utils/format'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const item = ref<Constitution | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const rules = computed(() => item.value?.active_version?.rules ?? [])

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    item.value = await constitutionsApi.getConstitution(String(route.params.id))
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
          {{ item?.name || t('constitutions.detailTitle') }}
        </h1>
        <p class="page-header__subtitle">
          {{ item?.description || t('constitutions.subtitle') }}
        </p>
      </div>
      <div class="page-header__actions">
        <button
          type="button"
          class="btn btn--secondary btn--sm"
          @click="router.push({ name: 'constitutions' })"
        >
          {{ t('common.back') }}
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
      v-else-if="item"
      class="stack"
    >
      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('constitutions.metaTitle') }}
        </div>
        <div class="card-panel__body meta-grid">
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('constitutions.colStatus') }}
            </div>
            <div class="meta-item__value">
              <span :class="statusBadgeClass(item.status)">{{ item.status }}</span>
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('constitutions.version') }}
            </div>
            <div class="meta-item__value">
              v{{ item.active_version?.version_number ?? '—' }}
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-item__label">
              {{ t('constitutions.colUpdated') }}
            </div>
            <div class="meta-item__value">
              {{ formatDate(item.updated_at || item.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <div class="card-panel">
        <div class="card-panel__header">
          {{ t('constitutions.rulesTitle') }}
          <span class="badge badge--brand">{{ rules.length }}</span>
        </div>
        <div class="card-panel__body">
          <div
            v-if="rules.length === 0"
            class="empty-state"
          >
            {{ t('constitutions.noRules') }}
          </div>
          <div
            v-else
            class="rule-list"
          >
            <div
              v-for="rule in rules"
              :key="rule.id || rule.rule_number"
              class="rule-item"
            >
              <div class="rule-item__num">
                #{{ rule.rule_number }}
              </div>
              <div>
                <div class="rule-item__name">
                  {{ rule.name }}
                </div>
                <div class="rule-item__meta">
                  {{ rule.category }} · {{ rule.field }} {{ rule.operator }}
                  {{ typeof rule.value === 'object' ? JSON.stringify(rule.value) : rule.value }}
                </div>
              </div>
              <span :class="statusBadgeClass(rule.action)">{{ rule.action }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
