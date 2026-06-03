<script setup lang="ts">
import type { WeightVector } from '@/stores/user'

defineProps<{ weights: WeightVector }>()

const labels: Record<keyof WeightVector, string> = {
  aptitude: 'Aptitude',
  personality_fit: 'Personality',
  nlp_similarity: 'Text Analysis',
  market_demand: 'Market Demand',
}
</script>

<template>
  <div class="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
    <h3 class="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-3">Weight Vector</h3>
    <ul class="space-y-3">
      <li v-for="(value, key) in weights" :key="key">
        <div class="flex justify-between text-xs mb-1">
          <span class="text-neutral-400">{{ labels[key as keyof WeightVector] }}</span>
          <span class="text-neutral-300 tabular-nums">{{ (value * 100).toFixed(1) }}%</span>
        </div>
        <div class="h-1 bg-neutral-800 rounded-full overflow-hidden">
          <div
            class="h-1 bg-indigo-500 rounded-full transition-all duration-500"
            :style="{ width: `${(value * 100).toFixed(0)}%` }"
          />
        </div>
      </li>
    </ul>
    <p class="text-xs text-neutral-600 mt-3">Updated via feedback · sums to 100%</p>
  </div>
</template>
