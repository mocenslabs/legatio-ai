<script setup lang="ts">
import { computed, ref } from 'vue'

import { avatarColor, avatarUrl, initialsFromUser } from '@/utils/avatar'

const props = withDefaults(
  defineProps<{
    seed: string
    firstName?: string
    lastName?: string
    email?: string
    size?: 'sm' | 'md' | 'lg'
  }>(),
  {
    firstName: '',
    lastName: '',
    email: '',
    size: 'md',
  },
)

const imgFailed = ref(false)

const initials = computed(() =>
  initialsFromUser({
    first_name: props.firstName,
    last_name: props.lastName,
    email: props.email,
  }),
)

const src = computed(() => avatarUrl(props.seed || props.email || 'user', 96))

const bg = computed(() => avatarColor(props.seed || props.email || 'user'))

function onError(): void {
  imgFailed.value = true
}
</script>

<template>
  <span
    class="user-avatar"
    :class="[`user-avatar--${size}`]"
    :style="imgFailed ? { backgroundColor: bg } : undefined"
    aria-hidden="true"
  >
    <img
      v-if="!imgFailed"
      :src="src"
      alt=""
      class="user-avatar__img"
      @error="onError"
    >
    <span
      v-else
      class="user-avatar__initials"
    >{{ initials }}</span>
  </span>
</template>
