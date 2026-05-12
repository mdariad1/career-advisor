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

// Demographics (stored separately; never used in scoring pipeline)
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
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12">
    <div class="bg-white p-8 rounded-xl shadow-sm w-full max-w-lg">
      <h1 class="text-2xl font-semibold text-gray-800 mb-6">Create account</h1>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm text-gray-600 mb-1">Full name</label>
          <input v-model="fullName" type="text" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">Email</label>
          <input v-model="email" type="email" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">Password</label>
          <input v-model="password" type="password" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>

        <fieldset class="border border-gray-200 rounded-lg p-4 space-y-3">
          <legend class="text-xs text-gray-500 px-1">
            Demographic information — collected for fairness auditing only, never used in recommendations
          </legend>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-gray-600 mb-1">Gender</label>
              <input v-model="gender" type="text" class="w-full border border-gray-200 rounded px-2 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1">Age group</label>
              <select v-model="ageGroup" class="w-full border border-gray-200 rounded px-2 py-1.5 text-sm">
                <option value="">Prefer not to say</option>
                <option>18–21</option>
                <option>22–25</option>
                <option>26–30</option>
                <option>31+</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1">Field of study</label>
              <input v-model="fieldOfStudy" type="text" class="w-full border border-gray-200 rounded px-2 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1">Socioeconomic background</label>
              <select v-model="socioeconomicBackground" class="w-full border border-gray-200 rounded px-2 py-1.5 text-sm">
                <option value="">Prefer not to say</option>
                <option>Low</option>
                <option>Middle</option>
                <option>High</option>
              </select>
            </div>
          </div>
        </fieldset>

        <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>
        <button type="submit" :disabled="loading" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {{ loading ? 'Creating account…' : 'Create account' }}
        </button>
      </form>

      <p class="text-sm text-gray-500 mt-4 text-center">
        Already have an account?
        <RouterLink to="/login" class="text-blue-600 hover:underline">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>
