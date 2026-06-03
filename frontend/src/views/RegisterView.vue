<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const fullName = ref('')
const email = ref('')
const password = ref('')

const gender = ref('')
const ageGroup = ref('')
const fieldOfStudy = ref('')
const socioeconomicBackground = ref('')

const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await api.post('/auth/register', {
      full_name: fullName.value,
      email: email.value,
      password: password.value,
      demographics: {
        gender: gender.value,
        age_group: ageGroup.value,
        field_of_study: fieldOfStudy.value,
        socioeconomic_background: socioeconomicBackground.value,
      },
    })
    await auth.login(email.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const inputClass = 'w-full bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-indigo-500 transition-colors'
const selectClass = 'w-full bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-indigo-500 transition-colors'
const labelClass = 'block text-xs text-neutral-500 mb-1.5 uppercase tracking-wide'
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-neutral-950 px-4 py-12">
    <div class="w-full max-w-md">
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-neutral-100">Create account</h1>
        <p class="text-sm text-neutral-500 mt-1">Career Advisor</p>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label :class="labelClass">Full name</label>
          <input v-model="fullName" type="text" required :class="inputClass" />
        </div>
        <div>
          <label :class="labelClass">Email</label>
          <input v-model="email" type="email" required :class="inputClass" />
        </div>
        <div>
          <label :class="labelClass">Password</label>
          <input v-model="password" type="password" required :class="inputClass" />
        </div>

        <div class="border border-neutral-800 rounded-lg p-4 space-y-3">
          <p class="text-xs text-neutral-600">
            Demographic information — for fairness auditing only, never used in recommendations.
          </p>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label :class="labelClass">Gender</label>
              <input v-model="gender" type="text" :class="inputClass" placeholder="Optional" />
            </div>
            <div>
              <label :class="labelClass">Age group</label>
              <select v-model="ageGroup" :class="selectClass">
                <option value="">Prefer not to say</option>
                <option>18–21</option>
                <option>22–25</option>
                <option>26–30</option>
                <option>31+</option>
              </select>
            </div>
            <div>
              <label :class="labelClass">Field of study</label>
              <input v-model="fieldOfStudy" type="text" :class="inputClass" placeholder="Optional" />
            </div>
            <div>
              <label :class="labelClass">Socioeconomic</label>
              <select v-model="socioeconomicBackground" :class="selectClass">
                <option value="">Prefer not to say</option>
                <option>Low</option>
                <option>Middle</option>
                <option>High</option>
              </select>
            </div>
          </div>
        </div>

        <p v-if="error" class="text-red-400 text-xs">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          {{ loading ? 'Creating account…' : 'Create account' }}
        </button>
      </form>

      <p class="text-sm text-neutral-600 mt-6 text-center">
        Already have an account?
        <RouterLink to="/login" class="text-indigo-400 hover:text-indigo-300 transition-colors">
          Sign in
        </RouterLink>
      </p>
    </div>
  </div>
</template>
