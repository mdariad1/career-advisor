<script setup lang="ts">
import type { WeightVector } from '@/stores/user'

defineProps<{ weights: WeightVector }>()

const labels: Record<keyof WeightVector, string> = {
  aptitude: 'Aptitude',
  personality_fit: 'Personality Fit',
  nlp_similarity: 'Text Analysis',
  market_demand: 'Market Demand',
}
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Current Weight Vector</h3>
    <ul class="space-y-2">
      <li v-for="(value, key) in weights" :key="key" class="flex items-center gap-3">
        <span class="w-32 text-xs text-gray-600">{{ labels[key as keyof WeightVector] }}</span>
        <div class="flex-1 bg-gray-100 rounded-full h-2">
          <div
            class="bg-blue-500 h-2 rounded-full transition-all duration-500"
            :style="{ width: `${(value * 100).toFixed(0)}%` }"
          />
        </div>
        <span class="text-xs text-gray-700 w-10 text-right">{{ (value * 100).toFixed(1) }}%</span>
      </li>
    </ul>
    <p class="text-xs text-gray-400 mt-3">
      Updated via your feedback. Weights sum to 100%.
    </p>
  </div>
</template>
