<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppNav v-if="auth.isAuthenticated" />
    <main class="flex-1">
      <RouterView />
    </main>
  </div>
</template>
