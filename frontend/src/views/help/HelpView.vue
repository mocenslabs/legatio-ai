<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm, locale } = useI18n()

const steps = computed(() => {
  void locale.value
  return tm('help.steps') as Array<{ title: string; body: string }>
})

const faqs = computed(() => {
  void locale.value
  return tm('help.faqs') as Array<{ q: string; a: string }>
})
</script>

<template>
  <div class="help-page">
    <div class="page-header">
      <div>
        <h1 class="page-header__title">
          {{ t('help.title') }}
        </h1>
        <p class="page-header__subtitle">
          {{ t('help.subtitle') }}
        </p>
      </div>
    </div>

    <section class="card-panel help-section">
      <div class="card-panel__header">
        {{ t('help.howTitle') }}
      </div>
      <div class="card-panel__body">
        <ol class="help-steps">
          <li
            v-for="(step, i) in steps"
            :key="i"
            class="help-step"
          >
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
      <div class="card-panel__header">
        {{ t('help.faqTitle') }}
      </div>
      <div class="card-panel__body stack">
        <details
          v-for="(faq, i) in faqs"
          :key="`${locale}-${i}`"
          class="help-faq"
        >
          <summary>{{ faq.q }}</summary>
          <p>{{ faq.a }}</p>
        </details>
      </div>
    </section>
  </div>
</template>
