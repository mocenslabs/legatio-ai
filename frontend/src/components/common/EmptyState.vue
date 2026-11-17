<script setup lang="ts">
defineProps<{
  title: string
  body?: string
}>()
</script>

<template>
  <div class="empty-state">
    <strong>{{ title }}</strong>
    <p v-if="body">
      {{ body }}
    </p>
    <div
      v-if="$slots.actions"
      class="empty-state__actions"
    >
      <slot name="actions" />
    </div>
  </div>
</template>
