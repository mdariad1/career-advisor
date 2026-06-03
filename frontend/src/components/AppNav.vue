<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <nav class="bg-neutral-900 border-b border-neutral-800 px-6 py-3 flex items-center justify-between">
    <RouterLink to="/" class="font-semibold text-neutral-100 tracking-tight">
      Career Advisor
    </RouterLink>

    <div class="flex items-center gap-6 text-sm">
      <RouterLink
        to="/"
        class="text-neutral-400 hover:text-neutral-100 transition-colors"
        active-class="text-neutral-100"
      >
        Dashboard
      </RouterLink>
      <RouterLink
        to="/assessment"
        class="text-neutral-400 hover:text-neutral-100 transition-colors"
        active-class="text-neutral-100"
      >
        Assessment
      </RouterLink>
      <RouterLink
        to="/recommendations"
        class="text-neutral-400 hover:text-neutral-100 transition-colors"
        active-class="text-neutral-100"
      >
        Recommendations
      </RouterLink>
      <RouterLink
        to="/jobs"
        class="text-neutral-400 hover:text-neutral-100 transition-colors"
        active-class="text-neutral-100"
      >
        Jobs
      </RouterLink>
      <RouterLink
        v-if="auth.role === 'admin'"
        to="/audit"
        class="text-neutral-400 hover:text-neutral-100 transition-colors"
        active-class="text-neutral-100"
      >
        Audit
      </RouterLink>
      <button
        @click="handleLogout"
        class="text-neutral-500 hover:text-red-400 transition-colors text-sm"
      >
        Logout
      </button>
    </div>
  </nav>
</template>
