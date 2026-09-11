<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue'
</script>

<template>
  <div class="flex items-center gap-2 font-bold text-lg tracking-tight select-none">
    <ShieldCheck class="h-6 w-6 text-primary" :stroke-width="2" />
    <span class="text-foreground">Legatio</span>
    <span class="text-accent text-xs font-semibold tracking-widest uppercase opacity-90">AI</span>
  </div>
</template>
