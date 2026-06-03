<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'

interface Job {
  job_id: string
  title: string
  company: string
  industry: string
  country_code: string
  salary_range: string | null
  skills: string[]
  synced_at: string
}

const jobs = ref<Job[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref('')
const industryFilter = ref('')
const countryFilter = ref('')

async function fetchJobs() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/jobs/', {
      params: {
        industry: industryFilter.value || undefined,
        country_code: countryFilter.value || undefined,
      },
    })
    jobs.value = data.jobs
    total.value = data.total
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchJobs)
</script>

<template>
  <div class="max-w-4xl mx-auto py-10 px-6 space-y-6">
    <div>
      <h1 class="text-xl font-semibold text-neutral-100">Job Listings</h1>
      <p class="text-sm text-neutral-500 mt-1">Live listings from JobDataPool.</p>
    </div>

    <!-- Filters -->
    <div class="flex gap-2">
      <input
        v-model="industryFilter"
        type="text"
        placeholder="Industry"
        class="flex-1 bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-indigo-600 transition-colors"
      />
      <input
        v-model="countryFilter"
        type="text"
        placeholder="Country (e.g. GB)"
        class="w-36 bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-indigo-600 transition-colors"
      />
      <button
        @click="fetchJobs"
        class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
      >
        Search
      </button>
    </div>

    <div v-if="loading" class="text-neutral-600 text-sm py-8 text-center">Loading jobs…</div>
    <p v-else-if="error" class="text-red-400 text-sm">{{ error }}</p>

    <template v-else>
      <p class="text-xs text-neutral-600">{{ total }} result{{ total !== 1 ? 's' : '' }}</p>

      <p v-if="jobs.length === 0" class="text-neutral-600 text-sm py-8 text-center">
        No jobs found.
      </p>

      <ul v-else class="space-y-2">
        <li
          v-for="job in jobs"
          :key="job.job_id"
          class="bg-neutral-900 border border-neutral-800 rounded-lg p-4 space-y-2"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h2 class="font-medium text-neutral-100 truncate">{{ job.title }}</h2>
              <p class="text-xs text-neutral-500 mt-0.5">
                {{ job.company }} · {{ job.industry }}
              </p>
            </div>
            <span class="text-xs text-neutral-600 shrink-0">{{ job.country_code }}</span>
          </div>

          <p v-if="job.salary_range" class="text-xs text-neutral-400">{{ job.salary_range }}</p>

          <div v-if="job.skills.length" class="flex flex-wrap gap-1">
            <span
              v-for="skill in job.skills"
              :key="skill"
              class="bg-neutral-800 text-neutral-400 text-xs px-2 py-0.5 rounded"
            >
              {{ skill }}
            </span>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>
