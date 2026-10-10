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

const steps = computed(() => {
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

const nextStep = computed(() => steps.value.find((s) => !s.done || s.pending))

const cards = computed(() => [
  {
    title: t('dashboard.cards.agents'),
    desc: t('dashboard.cards.agentsDesc'),
    to: { name: 'agents' },
  },
  {
    title: t('dashboard.cards.constitutions'),
    desc: t('dashboard.cards.constitutionsDesc'),
    to: { name: 'constitutions' },
  },
  {
    title: t('dashboard.cards.negotiations'),
    desc: t('dashboard.cards.negotiationsDesc'),
    to: { name: 'negotiations' },
  },
  {
    title: t('dashboard.cards.approvals'),
    desc: t('dashboard.cards.approvalsDesc'),
    to: { name: 'approvals' },
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
    const mine = agents.filter((a) => String(a.agent_type).toUpperCase().includes('USER'))
    counts.value = {
      agents: mine.length,
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
  <div class="dashboard">
    <section class="dashboard__hero">
      <h1>
        {{
          displayName
            ? t('dashboard.welcome', { name: displayName })
            : t('dashboard.welcomeGuest')
        }}
      </h1>
      <p>{{ t('dashboard.subtitleGuide') }}</p>
    </section>

    <section class="card-panel">
      <div class="card-panel__header">
        {{ t('dashboard.checklistTitle') }}
      </div>
      <div class="card-panel__body">
        <div
          v-if="loading"
          class="loading-block"
        >
          {{ t('common.loading') }}
        </div>
        <template v-else>
          <ul class="checklist">
            <li
              v-for="step in steps"
              :key="step.id"
            >
              <RouterLink
                :to="step.to"
                class="checklist__item"
                :class="{ 'is-done': step.done && !step.pending }"
              >
                <span class="checklist__mark">{{ step.done && !step.pending ? '✓' : '' }}</span>
                <div class="checklist__body">
                  <strong>{{ step.title }}</strong>
                  <span>{{ step.desc }}</span>
                </div>
                <span class="checklist__cta">{{ step.cta }}</span>
              </RouterLink>
            </li>
          </ul>
          <div
            v-if="nextStep"
            class="next-step"
          >
            <p>{{ t('dashboard.nextHint', { step: nextStep.title }) }}</p>
            <button
              type="button"
              class="btn btn--primary btn--sm"
              @click="router.push(nextStep.to)"
            >
              {{ nextStep.cta }}
            </button>
          </div>
        </template>
      </div>
    </section>

    <section class="dashboard__grid">
      <RouterLink
        v-for="card in cards"
        :key="card.title"
        :to="card.to"
        class="dashboard__card"
      >
        <h2>{{ card.title }}</h2>
        <p>{{ card.desc }}</p>
        <span class="dashboard__badge">{{ t('common.open') }}</span>
      </RouterLink>
    </section>
  </div>
</template>
