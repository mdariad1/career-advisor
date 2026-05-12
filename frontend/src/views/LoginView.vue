<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="bg-white p-8 rounded-xl shadow-sm w-full max-w-md">
      <h1 class="text-2xl font-semibold text-gray-800 mb-6">Sign in</h1>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm text-gray-600 mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">Password</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <p class="text-sm text-gray-500 mt-4 text-center">
        No account?
        <RouterLink to="/register" class="text-blue-600 hover:underline">Register</RouterLink>
      </p>
    </div>
  </div>
</template>
