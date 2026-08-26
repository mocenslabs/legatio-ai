<script setup lang="ts">
import { Button } from '@/components/ui/button'
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-background">
    <div class="text-center space-y-6">
      <h1 class="text-4xl font-bold tracking-tight">Legatio AI</h1>
      <p class="text-lg text-muted-foreground max-w-md">
        Your AI agent. Your rules. Negotiations that respect your Constitution.
      </p>
      <div class="flex gap-3 justify-center">
        <Button as-child>
          <router-link to="/register">Get Started</router-link>
        </Button>
        <Button variant="outline" as-child>
          <router-link to="/login">Sign In</router-link>
        </Button>
      </div>
    </div>
  </div>
</template>
