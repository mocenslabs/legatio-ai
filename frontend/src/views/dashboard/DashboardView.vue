<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import * as agentsApi from '@/api/agents'
import * as approvalsApi from '@/api/approvals'
import * as constitutionsApi from '@/api/constitutions'
import * as negotiationsApi from '@/api/negotiations'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const counts = ref({
  agents: 0,
  constitutions: 0,
  negotiations: 0,
  approvals: 0,
})
const loading = ref(true)

const displayName = computed(() => {
  const u = auth.user
  if (!u) return ''
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
  return name || u.email
})

type Step = {
  id: string
  done: boolean
  pending?: boolean
  title: string
  desc: string
  to: { name: string }
  cta: string
}

const steps = computed<Step[]>(() => {
  const c = counts.value
  return [
    {
      id: 'agent',
      done: c.agents > 0,
      title: t('dashboard.checklist.agentTitle'),
      desc: t('dashboard.checklist.agentDesc'),
      to: c.agents > 0 ? { name: 'agents' } : { name: 'agent-create' },
      cta: c.agents > 0 ? t('common.open') : t('dashboard.checklist.doIt'),
    },
    {
      id: 'constitution',
      done: c.constitutions > 0,
      title: t('dashboard.checklist.constitutionTitle'),
      desc: t('dashboard.checklist.constitutionDesc'),
      to: c.constitutions > 0 ? { name: 'constitutions' } : { name: 'constitution-create' },
      cta: c.constitutions > 0 ? t('common.open') : t('dashboard.checklist.doIt'),
    },
    {
      id: 'negotiation',
      done: c.negotiations > 0,
      title: t('dashboard.checklist.negotiationTitle'),
      desc: t('dashboard.checklist.negotiationDesc'),
      to: c.negotiations > 0 ? { name: 'negotiations' } : { name: 'negotiation-create' },
      cta: c.negotiations > 0 ? t('common.open') : t('dashboard.checklist.doIt'),
    },
    {
      id: 'approval',
      done: c.approvals === 0 && c.negotiations > 0,
      pending: c.approvals > 0,
      title: t('dashboard.checklist.approvalTitle'),
      desc:
        c.approvals > 0
          ? t('dashboard.checklist.approvalPending', { n: c.approvals })
          : t('dashboard.checklist.approvalDesc'),
      to: { name: 'approvals' },
      cta: c.approvals > 0 ? t('dashboard.checklist.review') : t('common.open'),
    },
  ]
})

const nextStep = computed(() => steps.value.find((s) => s.pending || !s.done))

const cards = computed(() => [
  {
    title: t('dashboard.cards.agents'),
    value: counts.value.agents,
    to: { name: 'agents' },
    highlight: false,
  },
  {
    title: t('dashboard.cards.constitutions'),
    value: counts.value.constitutions,
    to: { name: 'constitutions' },
    highlight: false,
  },
  {
    title: t('dashboard.cards.negotiations'),
    value: counts.value.negotiations,
    to: { name: 'negotiations' },
    highlight: false,
  },
  {
    title: t('dashboard.cards.approvals'),
    value: counts.value.approvals,
    to: { name: 'approvals' },
    highlight: counts.value.approvals > 0,
  },
])

async function load(): Promise<void> {
  loading.value = true
  try {
    const [agents, constitutions, negotiations, approvals] = await Promise.all([
      agentsApi.listAgents().catch(() => []),
      constitutionsApi.listConstitutions().catch(() => []),
      negotiationsApi.listNegotiations().catch(() => []),
      approvalsApi.listPendingApprovals().catch(() => []),
    ])
    counts.value = {
      agents: agents.length,
      constitutions: constitutions.length,
      negotiations: negotiations.length,
      approvals: approvals.length,
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="dash">
    <div class="page-header">
      <div>
        <h1 class="page-header__title">
          {{ t('dashboard.welcome', { name: displayName }) }}
        </h1>
        <p class="page-header__subtitle">{{ t('dashboard.subtitle') }}</p>
      </div>
    </div>

    <div v-if="counts.approvals > 0" class="dash-banner" role="status">
      <div>
        <p class="dash-banner__title">
          {{ t('dashboard.attentionTitle', { n: counts.approvals }) }}
        </p>
        <p class="dash-banner__body">{{ t('dashboard.attentionBody') }}</p>
      </div>
      <button
        type="button"
        class="btn btn--primary btn--sm"
        @click="router.push({ name: 'approvals' })"
      >
        {{ t('dashboard.checklist.review') }}
      </button>
    </div>

    <div class="dash-stats">
      <button
        v-for="card in cards"
        :key="card.title"
        type="button"
        class="dash-stat"
        :class="{ 'dash-stat--alert': card.highlight }"
        @click="router.push(card.to)"
      >
        <span class="dash-stat__label">{{ card.title }}</span>
        <span class="dash-stat__value">{{ loading ? '…' : card.value }}</span>
      </button>
    </div>

    <div v-if="nextStep && !loading" class="dash-next">
      <div class="dash-next__label">{{ t('dashboard.nextLabel') }}</div>
      <p class="dash-next__title">{{ nextStep.title }}</p>
      <p class="dash-next__body">{{ nextStep.desc }}</p>
      <button
        type="button"
        class="btn btn--primary btn--sm dash-next__btn"
        @click="router.push(nextStep.to)"
      >
        {{ nextStep.cta }}
      </button>
    </div>

    <div class="card-panel">
      <div class="card-panel__header">{{ t('dashboard.checklistTitle') }}</div>
      <div class="card-panel__body">
        <div v-if="loading" class="loading-block">{{ t('common.loading') }}</div>
        <ul v-else class="dash-list">
          <li
            v-for="step in steps"
            :key="step.id"
            class="dash-item"
            :class="{
              'dash-item--done': step.done && !step.pending,
              'dash-item--pending': step.pending,
            }"
          >
            <span class="dash-item__mark" aria-hidden="true">
              {{ step.pending ? '!' : step.done ? '✓' : '·' }}
            </span>
            <div class="dash-item__text">
              <p class="dash-item__title">{{ step.title }}</p>
              <p class="dash-item__desc">{{ step.desc }}</p>
            </div>
            <button
              type="button"
              class="btn btn--secondary btn--sm dash-item__btn"
              @click="router.push(step.to)"
            >
              {{ step.cta }}
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dash {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  width: 100%;
  max-width: 100%;
}

.dash-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.2rem;
  border-radius: 12px;
  border: 1px solid rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.12);
}

.dash-banner__title {
  margin: 0 0 0.25rem;
  font-weight: 600;
}

.dash-banner__body {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

.dash-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
  width: 100%;
}

.dash-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
  margin: 0;
  padding: 1rem 1.1rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  text-align: left;
  cursor: pointer;
  font: inherit;
}

.dash-stat:hover {
  border-color: rgba(14, 165, 233, 0.45);
}

.dash-stat__label {
  font-size: 0.8rem;
  opacity: 0.72;
  line-height: 1.2;
}

.dash-stat__value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.1;
}

.dash-stat--alert .dash-stat__value {
  color: #f59e0b;
}

.dash-next {
  padding: 1rem 1.2rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.dash-next__label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.65;
  margin-bottom: 0.35rem;
}

.dash-next__title {
  margin: 0 0 0.25rem;
  font-weight: 600;
}

.dash-next__body {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  opacity: 0.88;
}

.dash-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.dash-item {
  display: grid;
  grid-template-columns: 1.75rem minmax(0, 1fr) auto;
  gap: 0.75rem 1rem;
  align-items: center;
  padding: 0.95rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.dash-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.dash-item:first-child {
  padding-top: 0;
}

.dash-item__mark {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.06);
}

.dash-item--done .dash-item__mark {
  background: rgba(34, 197, 94, 0.25);
  color: #22c55e;
}

.dash-item--pending .dash-item__mark {
  background: rgba(245, 158, 11, 0.25);
  color: #f59e0b;
}

.dash-item__text {
  min-width: 0;
}

.dash-item__title {
  margin: 0 0 0.15rem;
  font-weight: 600;
  font-size: 0.95rem;
}

.dash-item__desc {
  margin: 0;
  font-size: 0.85rem;
  opacity: 0.8;
  line-height: 1.35;
}

.dash-item__btn {
  white-space: nowrap;
}

/* Light theme: borders slightly stronger */
:global([data-theme='light']) .dash-stat,
:global([data-theme='light']) .dash-next,
:global([data-theme='light']) .dash-item {
  border-color: rgba(0, 0, 0, 0.08);
}

:global([data-theme='light']) .dash-stat {
  background: rgba(0, 0, 0, 0.02);
}

@media (max-width: 960px) {
  .dash-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .dash-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.65rem;
  }

  .dash-stat {
    padding: 0.85rem 0.9rem;
  }

  .dash-stat__value {
    font-size: 1.45rem;
  }

  .dash-item {
    grid-template-columns: 1.75rem minmax(0, 1fr);
    grid-template-areas:
      'mark text'
      'btn btn';
  }

  .dash-item__mark {
    grid-area: mark;
  }

  .dash-item__text {
    grid-area: text;
  }

  .dash-item__btn {
    grid-area: btn;
    width: 100%;
  }

  .dash-banner {
    flex-direction: column;
    align-items: stretch;
  }

  .dash-banner .btn,
  .dash-next__btn {
    width: 100%;
  }
}
</style>
