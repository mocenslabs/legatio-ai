<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import LocaleSwitch from '@/components/common/LocaleSwitch.vue'
import ThemeSwitch from '@/components/common/ThemeSwitch.vue'
import { useAuthStore } from '@/stores/auth'

const { t, tm } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const pillars = tm('home.pillars') as Array<{ title: string; body: string }>
const flow = tm('home.flow') as Array<{ title: string; body: string }>

function goApp(): void {
  if (auth.isAuthenticated) {
    void router.push({ name: 'dashboard' })
  } else {
    void router.push({ name: 'login' })
  }
}
</script>

<template>
  <div class="home">
    <header class="home-nav">
      <div class="home-nav__brand">
        {{ t('app.name') }}
      </div>
      <div class="home-nav__actions">
        <ThemeSwitch />
        <LocaleSwitch />
        <button
          v-if="!auth.isAuthenticated"
          type="button"
          class="btn btn--ghost btn--sm"
          @click="router.push({ name: 'login' })"
        >
          {{ t('auth.submitLogin') }}
        </button>
        <button
          type="button"
          class="btn btn--primary btn--sm"
          @click="goApp"
        >
          {{ auth.isAuthenticated ? t('nav.dashboard') : t('home.cta') }}
        </button>
      </div>
    </header>

    <section class="home-hero">
      <p class="home-hero__eyebrow">
        {{ t('home.eyebrow') }}
      </p>
      <h1>{{ t('home.headline') }}</h1>
      <p class="home-hero__lead">
        {{ t('home.lead') }}
      </p>
      <div class="home-hero__cta">
        <button
          type="button"
          class="btn btn--primary"
          @click="goApp"
        >
          {{ t('home.cta') }}
        </button>
        <button
          type="button"
          class="btn btn--secondary"
          @click="router.push({ name: 'help' })"
        >
          {{ t('home.ctaHelp') }}
        </button>
      </div>
    </section>

    <section class="home-pillars">
      <article
        v-for="(p, i) in pillars"
        :key="i"
        class="home-pillar"
      >
        <h2>{{ p.title }}</h2>
        <p>{{ p.body }}</p>
      </article>
    </section>

    <section class="home-flow-wrap">
      <h2 class="home-section-title">
        {{ t('home.flowTitle') }}
      </h2>
      <div class="home-flow">
        <div
          v-for="(f, i) in flow"
          :key="i"
          class="home-flow__item"
        >
          <span class="home-flow__num">{{ i + 1 }}</span>
          <h3>{{ f.title }}</h3>
          <p>{{ f.body }}</p>
        </div>
      </div>
    </section>

    <section class="home-bottom">
      <h2>{{ t('home.bottomTitle') }}</h2>
      <p>{{ t('home.bottomBody') }}</p>
      <button
        type="button"
        class="btn btn--primary"
        @click="goApp"
      >
        {{ t('home.cta') }}
      </button>
    </section>

    <footer class="home-footer">
      <span>{{ t('app.name') }}</span>
      <span class="home-footer__muted">{{ t('app.tagline') }}</span>
    </footer>
  </div>
</template>
