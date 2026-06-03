<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'

interface Metric {
  attribute: string
  disparate_impact_ratio: number
  equal_opportunity_score: number
  flagged: boolean
}

interface AuditReport {
  id: string
  created_at: string
  metrics: Metric[]
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
  <div class="max-w-4xl mx-auto py-10 px-6 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-neutral-100">Bias Audit</h1>
        <p class="text-sm text-neutral-500 mt-1">Disparate impact and equal opportunity scores — admin only.</p>
      </div>
      <button
        @click="runAudit"
        :disabled="running"
        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
      >
        {{ running ? 'Running…' : 'Run Audit' }}
      </button>
    </div>

    <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>
    <div v-if="loading" class="text-neutral-600 text-sm py-8 text-center">Loading reports…</div>

    <div v-if="reports.length === 0 && !loading" class="text-neutral-600 text-sm py-8 text-center">
      No reports yet. Run an audit to generate the first report.
    </div>

    <div
      v-for="report in reports"
      :key="report.id"
      class="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden"
    >
      <div class="px-5 py-3 border-b border-neutral-800">
        <p class="text-xs text-neutral-500">
          Generated {{ new Date(report.created_at).toLocaleString() }}
        </p>
      </div>

      <table class="w-full text-sm">
        <thead>
          <tr class="text-left border-b border-neutral-800">
            <th class="px-5 py-2.5 text-xs font-medium text-neutral-500 uppercase tracking-wide">Attribute</th>
            <th class="px-5 py-2.5 text-xs font-medium text-neutral-500 uppercase tracking-wide">DIR</th>
            <th class="px-5 py-2.5 text-xs font-medium text-neutral-500 uppercase tracking-wide">EOS</th>
            <th class="px-5 py-2.5 text-xs font-medium text-neutral-500 uppercase tracking-wide">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="m in report.metrics"
            :key="m.attribute"
            class="border-b border-neutral-800 last:border-0"
            :class="m.flagged ? 'bg-red-950/30' : ''"
          >
            <td class="px-5 py-3 text-neutral-300 capitalize">
              {{ m.attribute.replace(/_/g, ' ') }}
            </td>
            <td class="px-5 py-3 text-neutral-400 tabular-nums">{{ m.disparate_impact_ratio.toFixed(3) }}</td>
            <td class="px-5 py-3 text-neutral-400 tabular-nums">{{ m.equal_opportunity_score.toFixed(3) }}</td>
            <td class="px-5 py-3">
              <span
                :class="[
                  'text-xs px-2 py-0.5 rounded-full',
                  m.flagged
                    ? 'bg-red-950 text-red-400 border border-red-900'
                    : 'bg-neutral-800 text-neutral-400 border border-neutral-700',
                ]"
              >
                {{ m.flagged ? 'Below 0.80' : 'Pass' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
