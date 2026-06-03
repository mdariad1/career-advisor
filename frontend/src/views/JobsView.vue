<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'

interface Job {
  job_id: string
  title: string
  company: string
  industry: string
  country_code: string
  salary_range: string
  skills: string[]
  synced_at: string
}

const jobs = ref<Job[]>([])
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
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchJobs)
</script>

<template>
  <div class="max-w-4xl mx-auto py-10 px-4 space-y-6">
    <h1 class="text-2xl font-semibold text-gray-800">Job Listings</h1>
    <p class="text-sm text-gray-500">Live listings from JobDataPool, matched to your top career categories.</p>

    <div class="flex gap-3">
      <input
        v-model="industryFilter"
        type="text"
        placeholder="Filter by industry"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm flex-1"
      />
      <input
        v-model="countryFilter"
        type="text"
        placeholder="Country code (e.g. GB)"
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-40"
      />
      <button @click="fetchJobs" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
        Search
      </button>
    </div>

    <div v-if="loading" class="text-gray-400 text-sm">Loading jobs…</div>
    <p v-else-if="error" class="text-red-500 text-sm">{{ error }}</p>
    <p v-else-if="jobs.length === 0" class="text-gray-400 text-sm">No jobs found.</p>

    <ul class="space-y-3">
      <li
        v-for="job in jobs"
        :key="job.job_id"
        class="bg-white border border-gray-200 rounded-lg p-4 space-y-1"
      >
        <div class="flex justify-between">
          <h2 class="font-medium text-gray-800">{{ job.title }}</h2>
          <span class="text-xs text-gray-500">{{ job.country_code }}</span>
        </div>
        <p class="text-xs text-gray-500">{{ job.company }} · {{ job.industry }}</p>
        <p class="text-xs text-gray-600">{{ job.salary_range }}</p>
        <div class="flex flex-wrap gap-1 mt-1">
          <span
            v-for="skill in job.skills"
            :key="skill"
            class="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded"
          >
            {{ skill }}
          </span>
        </div>
      </li>
    </ul>
  </div>
</template>
