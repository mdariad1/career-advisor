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
  personality_fit: 'Personality',
  nlp_similarity: 'Text Analysis',
  market_demand: 'Market Demand',
}

const colours: Record<keyof ShapContributions, string> = {
  aptitude: 'bg-indigo-500',
  personality_fit: 'bg-indigo-400',
  nlp_similarity: 'bg-neutral-400',
  market_demand: 'bg-neutral-500',
}
</script>

<template>
  <div class="space-y-2">
    <ul class="space-y-2">
      <li
        v-for="(value, key) in contributions"
        :key="key"
        class="flex items-center gap-3 text-xs"
      >
        <span class="w-28 text-neutral-500 shrink-0">{{ labels[key as keyof ShapContributions] }}</span>
        <div class="flex-1 bg-neutral-800 rounded-full h-1">
          <div
            :class="['h-1 rounded-full transition-all duration-500', colours[key as keyof ShapContributions]]"
            :style="{ width: `${(value * 100).toFixed(0)}%` }"
          />
        </div>
        <span class="w-10 text-right text-neutral-400 tabular-nums">{{ (value * 100).toFixed(1) }}%</span>
      </li>
    </ul>
    <p class="text-xs text-neutral-600 italic pt-1">{{ explanation }}</p>
  </div>
</template>
