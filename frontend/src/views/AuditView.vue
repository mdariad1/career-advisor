<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'

interface AuditReport {
  id: string
  created_at: string
  metrics: {
    attribute: string
    disparate_impact_ratio: number
    equal_opportunity_score: number
    flagged: boolean
  }[]
}

const reports = ref<AuditReport[]>([])
const running = ref(false)
const loading = ref(true)
const error = ref('')

onMounted(fetchReports)

async function fetchReports() {
  loading.value = true
  try {
    const { data } = await api.get('/audit/reports')
    reports.value = data
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function runAudit() {
  running.value = true
  error.value = ''
  try {
    await api.post('/audit/run')
    await fetchReports()
  } catch (e: any) {
    error.value = e.message
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto py-10 px-4 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-gray-800">Bias Audit</h1>
        <p class="text-sm text-gray-500 mt-1">Disparate impact and equal opportunity scores — admin only.</p>
      </div>
      <button
        @click="runAudit"
        :disabled="running"
        class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {{ running ? 'Running…' : 'Run audit' }}
      </button>
    </div>

    <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
    <div v-if="loading" class="text-gray-400 text-sm">Loading reports…</div>

    <div v-for="report in reports" :key="report.id" class="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
      <p class="text-xs text-gray-400">Report generated {{ new Date(report.created_at).toLocaleString() }}</p>

      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-gray-500 border-b border-gray-100">
            <th class="pb-2">Attribute</th>
            <th class="pb-2">Disparate Impact Ratio</th>
            <th class="pb-2">Equal Opportunity Score</th>
            <th class="pb-2">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="m in report.metrics"
            :key="m.attribute"
            :class="['border-b border-gray-50', m.flagged ? 'bg-red-50' : '']"
          >
            <td class="py-2 text-gray-700 capitalize">{{ m.attribute.replace('_', ' ') }}</td>
            <td class="py-2">{{ m.disparate_impact_ratio.toFixed(3) }}</td>
            <td class="py-2">{{ m.equal_opportunity_score.toFixed(3) }}</td>
            <td class="py-2">
              <span
                :class="['text-xs px-2 py-0.5 rounded-full', m.flagged ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700']"
              >
                {{ m.flagged ? '⚠ Below 0.80' : 'Pass' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
