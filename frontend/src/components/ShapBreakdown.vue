<script setup lang="ts">
export interface ShapContributions {
  aptitude: number
  personality_fit: number
  nlp_similarity: number
  market_demand: number
}

defineProps<{
  contributions: ShapContributions
  explanation: string
}>()

const labels: Record<keyof ShapContributions, string> = {
  aptitude: 'Aptitude',
  personality_fit: 'Personality Fit',
  nlp_similarity: 'Text Analysis',
  market_demand: 'Market Demand',
}

const colours: Record<keyof ShapContributions, string> = {
  aptitude: 'bg-violet-400',
  personality_fit: 'bg-blue-400',
  nlp_similarity: 'bg-emerald-400',
  market_demand: 'bg-amber-400',
}
</script>

<template>
  <div class="space-y-2">
    <ul class="space-y-1">
      <li
        v-for="(value, key) in contributions"
        :key="key"
        class="flex items-center gap-3 text-xs"
      >
        <span class="w-28 text-gray-600">{{ labels[key as keyof ShapContributions] }}</span>
        <div class="flex-1 bg-gray-100 rounded-full h-1.5">
          <div
            :class="['h-1.5 rounded-full transition-all duration-500', colours[key as keyof ShapContributions]]"
            :style="{ width: `${value.toFixed(0)}%` }"
          />
        </div>
        <span class="w-8 text-right text-gray-700">{{ value.toFixed(0) }}%</span>
      </li>
    </ul>
    <p class="text-xs text-gray-500 italic">{{ explanation }}</p>
  </div>
</template>
