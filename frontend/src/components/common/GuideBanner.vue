<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const STORAGE_KEY = 'legatio_guide_banner_dismissed'

const { t } = useI18n()
const router = useRouter()
const visible = ref(false)

onMounted(() => {
  try {
    visible.value = localStorage.getItem(STORAGE_KEY) !== '1'
  } catch {
    visible.value = true
  }
})

function dismiss(): void {
  try {
    localStorage.setItem(STORAGE_KEY, '1')
  } catch {
    /* ignore */
  }
  visible.value = false
}

function go(name: string): void {
  void router.push({ name })
}
</script>

<template>
  <div
    v-if="visible"
    class="guide-banner"
    role="region"
    :aria-label="t('guide.aria')"
  >
    <div class="guide-banner__content">
      <p class="guide-banner__title">
        {{ t('guide.title') }}
      </p>
      <p class="guide-banner__body">
        {{ t('guide.body') }}
      </p>
      <ol class="guide-banner__steps">
        <li>
          <button
            type="button"
            class="guide-banner__link"
            @click="go('agent-create')"
          >
            {{ t('guide.stepAgent') }}
          </button>
        </li>
        <li>
          <button
            type="button"
            class="guide-banner__link"
            @click="go('constitution-create')"
          >
            {{ t('guide.stepConstitution') }}
          </button>
        </li>
        <li>
          <button
            type="button"
            class="guide-banner__link"
            @click="go('negotiation-create')"
          >
            {{ t('guide.stepNegotiate') }}
          </button>
        </li>
        <li>
          <button
            type="button"
            class="guide-banner__link"
            @click="go('approvals')"
          >
            {{ t('guide.stepApprove') }}
          </button>
        </li>
      </ol>
    </div>
    <div class="guide-banner__actions">
      <button
        type="button"
        class="btn btn--secondary btn--sm"
        @click="go('help')"
      >
        {{ t('guide.help') }}
      </button>
      <button
        type="button"
        class="btn btn--ghost btn--sm"
        @click="dismiss"
      >
        {{ t('guide.dismiss') }}
      </button>
    </div>
  </div>
</template>
