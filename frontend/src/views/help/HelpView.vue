<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t, tm, locale } = useI18n()
const router = useRouter()

const steps = computed(() => {
  void locale.value
  return tm('help.steps') as Array<{ title: string; body: string }>
})

const faqs = computed(() => {
  void locale.value
  return tm('help.faqs') as Array<{ q: string; a: string }>
})

const glossary = computed(() => {
  void locale.value
  return tm('help.glossary') as Array<{ term: string; meaning: string }>
})
</script>

<template>
  <div class="help-page">
    <div class="page-header">
      <div>
        <h1 class="page-header__title">{{ t('help.title') }}</h1>
        <p class="page-header__subtitle">{{ t('help.subtitle') }}</p>
      </div>
      <div class="page-header__actions">
        <button type="button" class="btn btn--primary btn--sm" @click="router.push({ name: 'dashboard' })">
          {{ t('help.backDashboard') }}
        </button>
      </div>
    </div>

    <section class="card-panel help-section">
      <div class="card-panel__header">{{ t('help.promiseTitle') }}</div>
      <div class="card-panel__body">
        <p>{{ t('help.promiseBody') }}</p>
      </div>
    </section>

    <section class="card-panel help-section">
      <div class="card-panel__header">{{ t('help.howTitle') }}</div>
      <div class="card-panel__body">
        <ol class="help-steps">
          <li v-for="(step, i) in steps" :key="i" class="help-step">
            <span class="help-step__num">{{ i + 1 }}</span>
            <div>
              <strong>{{ step.title }}</strong>
              <p>{{ step.body }}</p>
            </div>
          </li>
        </ol>
      </div>
    </section>

    <section class="card-panel help-section">
      <div class="card-panel__header">{{ t('help.rulesTitle') }}</div>
      <div class="card-panel__body stack">
        <p>{{ t('help.rulesIntro') }}</p>
        <div>
          <strong>{{ t('help.rulesHowTo') }}</strong>
          <p>{{ t('help.rulesHowToBody') }}</p>
        </div>
        <div>
          <strong>{{ t('help.rulesExampleTitle') }}</strong>
          <p>{{ t('help.rulesExampleBody') }}</p>
        </div>
        <p>{{ t('help.rulesActions') }}</p>
        <p class="page-header__subtitle">{{ t('help.rulesTip') }}</p>
      </div>
    </section>

    <section class="card-panel help-section">
      <div class="card-panel__header">{{ t('help.glossaryTitle') }}</div>
      <div class="card-panel__body stack">
        <div v-for="(g, i) in glossary" :key="i">
          <strong>{{ g.term }}</strong>
          <p class="page-header__subtitle">{{ g.meaning }}</p>
        </div>
      </div>
    </section>

    <section class="card-panel help-section">
      <div class="card-panel__header">{{ t('help.faqTitle') }}</div>
      <div class="card-panel__body stack">
        <details v-for="(faq, i) in faqs" :key="i" class="help-faq">
          <summary>{{ faq.q }}</summary>
          <p>{{ faq.a }}</p>
        </details>
      </div>
    </section>
  </div>
</template>
