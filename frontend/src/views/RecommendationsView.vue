<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useUserStore } from '@/stores/user'
import WeightPanel from '@/components/WeightPanel.vue'
import ShapBreakdown from '@/components/ShapBreakdown.vue'
import type { ShapContributions } from '@/components/ShapBreakdown.vue'

const user = useUserStore()

interface Recommendation {
  id: string
  career_title: string
  score: number
  contributions: ShapContributions
  explanation: string
  salary_range: string | null
  job_count: number
}

const recommendations = ref<Recommendation[]>([])
const loading = ref(true)
const generating = ref(false)
const noRecommendations = ref(false)
const error = ref('')

onMounted(async () => {
  await user.fetchWeights()
  await loadRecommendations()
})

async function loadRecommendations() {
  loading.value = true
  error.value = ''
  noRecommendations.value = false
  try {
    const { data } = await api.get('/recommendations/')
    recommendations.value = data.recommendations
  } catch (e: any) {
    if (e.message?.includes('No recommendations yet') || e.message?.includes('404')) {
      noRecommendations.value = true
    } else {
      error.value = e.message
    }
  } finally {
    loading.value = false
  }
}

async function generate() {
  generating.value = true
  error.value = ''
  try {
    const { data } = await api.post('/recommendations/')
    recommendations.value = data.recommendations
    noRecommendations.value = false
  } catch (e: any) {
    error.value = e.message
  } finally {
    generating.value = false
  }
}

async function sendFeedback(rec: Recommendation, action: 'accept' | 'reject') {
  try {
    const { data } = await api.post('/feedback/', { recommendation_id: rec.id, action })
    if (data.weights_after && user.profile) {
      user.profile.weights = data.weights_after
    }
  } catch (e: any) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto py-10 px-6">
    <div class="flex items-start gap-8">

      <!-- Main -->
      <div class="flex-1 space-y-5 min-w-0">
        <div class="flex items-center justify-between">
          <h1 class="text-xl font-semibold text-neutral-100">Career Recommendations</h1>
          <button
            v-if="recommendations.length > 0"
            @click="generate"
            :disabled="generating"
            class="text-xs text-neutral-500 hover:text-neutral-300 border border-neutral-800 hover:border-neutral-700 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
          >
            {{ generating ? 'Regenerating…' : 'Regenerate' }}
          </button>
        </div>

        <div v-if="loading" class="text-neutral-600 text-sm py-8 text-center">
          Loading recommendations…
        </div>

        <div v-else-if="noRecommendations"
             class="bg-neutral-900 border border-neutral-800 rounded-lg p-8 text-center space-y-4">
          <p class="text-neutral-400 text-sm">No recommendations yet.</p>
          <p class="text-neutral-600 text-xs">Complete your assessment, then generate your top career matches.</p>
          <button
            @click="generate"
            :disabled="generating"
            class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
          >
            {{ generating ? 'Generating…' : 'Generate Recommendations' }}
          </button>
        </div>

        <p v-else-if="error" class="text-red-400 text-sm">{{ error }}</p>

        <div
          v-for="(rec, idx) in recommendations"
          :key="rec.id"
          class="bg-neutral-900 border border-neutral-800 rounded-lg p-5 space-y-4"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0">
              <div class="flex items-baseline gap-2">
                <span class="text-xs text-neutral-600 font-mono tabular-nums">#{{ idx + 1 }}</span>
                <h2 class="text-base font-semibold text-neutral-100 truncate">{{ rec.career_title }}</h2>
              </div>
              <p class="text-xs text-neutral-500 mt-0.5">
                {{ (rec.score * 100).toFixed(1) }}% match
                <template v-if="rec.salary_range"> · {{ rec.salary_range }}</template>
                · {{ rec.job_count }} listings
              </p>
            </div>
            <div class="flex gap-1.5 shrink-0">
              <button
                @click="sendFeedback(rec, 'accept')"
                class="text-xs border border-neutral-700 text-neutral-400 hover:border-indigo-700 hover:text-indigo-300 px-3 py-1.5 rounded-lg transition-colors"
              >
                Accept
              </button>
              <button
                @click="sendFeedback(rec, 'reject')"
                class="text-xs border border-neutral-700 text-neutral-400 hover:border-red-900 hover:text-red-400 px-3 py-1.5 rounded-lg transition-colors"
              >
                Reject
              </button>
            </div>
          </div>

          <ShapBreakdown :contributions="rec.contributions" :explanation="rec.explanation" />
        </div>
      </div>

      <!-- Weight sidebar -->
      <aside class="w-56 shrink-0 sticky top-6">
        <WeightPanel v-if="user.profile" :weights="user.profile.weights" />
      </aside>
    </div>
  </div>
</template>
