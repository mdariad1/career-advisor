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
  salary_range: string
  job_count: number
}

const recommendations = ref<Recommendation[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const [recRes] = await Promise.all([
      api.get('/recommendations/'),
      user.fetchWeights(),
    ])
    recommendations.value = recRes.data
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

async function sendFeedback(rec: Recommendation, action: 'accept' | 'reject') {
  try {
    const { data } = await api.post('/feedback/', { recommendation_id: rec.id, action })
    if (data.weights && user.profile) {
      user.profile.weights = data.weights
    }
  } catch (e: any) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto py-10 px-4 space-y-8">
    <div class="flex items-start gap-8">
      <div class="flex-1 space-y-6">
        <h1 class="text-2xl font-semibold text-gray-800">Career Recommendations</h1>

        <div v-if="loading" class="text-gray-400 text-sm">Computing recommendations…</div>
        <p v-else-if="error" class="text-red-500 text-sm">{{ error }}</p>

        <div
          v-for="(rec, idx) in recommendations"
          :key="rec.id"
          class="bg-white border border-gray-200 rounded-lg p-5 space-y-4"
        >
          <div class="flex items-start justify-between">
            <div>
              <span class="text-xs text-gray-400 font-mono">#{{ idx + 1 }}</span>
              <h2 class="text-lg font-semibold text-gray-800">{{ rec.career_title }}</h2>
              <p class="text-xs text-gray-500">Score: {{ (rec.score * 100).toFixed(1) }}% · {{ rec.salary_range }} · {{ rec.job_count }} live listings</p>
            </div>
            <div class="flex gap-2">
              <button
                @click="sendFeedback(rec, 'accept')"
                class="text-xs bg-green-50 border border-green-200 text-green-700 px-3 py-1.5 rounded-lg hover:bg-green-100"
              >
                Accept
              </button>
              <button
                @click="sendFeedback(rec, 'reject')"
                class="text-xs bg-red-50 border border-red-200 text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-100"
              >
                Reject
              </button>
            </div>
          </div>

          <ShapBreakdown :contributions="rec.contributions" :explanation="rec.explanation" />
        </div>
      </div>

      <!-- Live weight panel (DO-1: always visible) -->
      <aside class="w-64 shrink-0 sticky top-6">
        <WeightPanel v-if="user.profile" :weights="user.profile.weights" />
      </aside>
    </div>
  </div>
</template>
