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
  <nav class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
    <RouterLink to="/" class="font-semibold text-gray-800 text-lg">Career Advisor</RouterLink>

    <div class="flex items-center gap-6 text-sm">
      <RouterLink to="/" class="text-gray-600 hover:text-gray-900">Dashboard</RouterLink>
      <RouterLink to="/assessment" class="text-gray-600 hover:text-gray-900">Assessment</RouterLink>
      <RouterLink to="/recommendations" class="text-gray-600 hover:text-gray-900">Recommendations</RouterLink>
      <RouterLink to="/jobs" class="text-gray-600 hover:text-gray-900">Jobs</RouterLink>
      <RouterLink v-if="auth.role === 'admin'" to="/audit" class="text-gray-600 hover:text-gray-900">Audit</RouterLink>
      <button @click="handleLogout" class="text-gray-500 hover:text-red-600">Logout</button>
    </div>
  </nav>
</template>
