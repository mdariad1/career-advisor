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
  <div class="min-h-screen flex items-center justify-center bg-neutral-950 px-4">
    <div class="w-full max-w-sm">
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-neutral-100">Sign in</h1>
        <p class="text-sm text-neutral-500 mt-1">Career Advisor</p>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-xs text-neutral-500 mb-1.5 uppercase tracking-wide">Email</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
        <div>
          <label class="block text-xs text-neutral-500 mb-1.5 uppercase tracking-wide">Password</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <p v-if="error" class="text-red-400 text-xs">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <p class="text-sm text-neutral-600 mt-6 text-center">
        No account?
        <RouterLink to="/register" class="text-indigo-400 hover:text-indigo-300 transition-colors">
          Register
        </RouterLink>
      </p>
    </div>
  </div>
</template>
