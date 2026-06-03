<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useUserStore } from '@/stores/user'
import WeightPanel from '@/components/WeightPanel.vue'

const user = useUserStore()

onMounted(() => user.fetchProfile())
</script>

<template>
  <div class="max-w-4xl mx-auto py-10 px-6 space-y-8">

    <div v-if="user.loading" class="text-neutral-600 text-sm">Loading profile…</div>

    <template v-else-if="user.profile">
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-xl font-semibold text-neutral-100">{{ user.profile.full_name }}</h1>
          <p class="text-sm text-neutral-500 mt-0.5">{{ user.profile.email }}</p>
        </div>
        <RouterLink
          to="/assessment"
          class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Take Assessment
        </RouterLink>
      </div>

      <!-- Profile stats -->
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <p class="text-xs text-neutral-500 mb-1">Aptitude Score</p>
          <p class="text-2xl font-semibold text-neutral-100 tabular-nums">
            {{ user.profile.aptitude_score != null
                ? `${(user.profile.aptitude_score * 100).toFixed(0)}%`
                : '—' }}
          </p>
        </div>
        <div class="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <p class="text-xs text-neutral-500 mb-1">Personality Profile</p>
          <p class="text-sm font-medium"
             :class="user.profile.ocean_vector ? 'text-neutral-100' : 'text-neutral-600'">
            {{ user.profile.ocean_vector ? 'Completed' : 'Not taken' }}
          </p>
        </div>
        <div class="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <p class="text-xs text-neutral-500 mb-1">NLP Labels</p>
          <p class="text-sm font-medium"
             :class="user.profile.nlp_labels?.length ? 'text-neutral-100' : 'text-neutral-600'">
            {{ user.profile.nlp_labels?.join(', ') || 'Not taken' }}
          </p>
        </div>
      </div>

      <WeightPanel :weights="user.profile.weights" />

      <!-- Quick links -->
      <div class="grid grid-cols-2 gap-3">
        <RouterLink
          to="/recommendations"
          class="bg-neutral-900 border border-neutral-800 hover:border-indigo-700 rounded-lg p-4 transition-colors group"
        >
          <p class="font-medium text-neutral-200 group-hover:text-neutral-100">Recommendations</p>
          <p class="text-xs text-neutral-600 mt-1">Top career matches with SHAP breakdown</p>
        </RouterLink>
        <RouterLink
          to="/jobs"
          class="bg-neutral-900 border border-neutral-800 hover:border-indigo-700 rounded-lg p-4 transition-colors group"
        >
          <p class="font-medium text-neutral-200 group-hover:text-neutral-100">Browse Jobs</p>
          <p class="text-xs text-neutral-600 mt-1">Live listings matched to your profile</p>
        </RouterLink>
      </div>
    </template>
  </div>
</template>
