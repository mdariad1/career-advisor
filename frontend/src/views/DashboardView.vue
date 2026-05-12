<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useUserStore } from '@/stores/user'
import WeightPanel from '@/components/WeightPanel.vue'

const user = useUserStore()

onMounted(() => user.fetchProfile())
</script>

<template>
  <div class="max-w-4xl mx-auto py-10 px-4 space-y-8">
    <div v-if="user.loading" class="text-gray-400 text-sm">Loading profile…</div>

    <template v-else-if="user.profile">
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-gray-800">Welcome, {{ user.profile.full_name }}</h1>
          <p class="text-sm text-gray-500 mt-1">{{ user.profile.email }}</p>
        </div>
        <RouterLink
          to="/assessment"
          class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Take Assessment
        </RouterLink>
      </div>

      <div class="grid grid-cols-3 gap-4">
        <div class="bg-white border border-gray-200 rounded-lg p-4 text-center">
          <p class="text-xs text-gray-500 mb-1">Aptitude Score</p>
          <p class="text-2xl font-bold text-gray-800">
            {{ user.profile.aptitude_score ?? '—' }}
          </p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-4 text-center">
          <p class="text-xs text-gray-500 mb-1">Personality Profile</p>
          <p class="text-sm text-gray-700">
            {{ user.profile.ocean_vector ? 'Completed' : 'Not yet taken' }}
          </p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-4 text-center">
          <p class="text-xs text-gray-500 mb-1">NLP Labels</p>
          <p class="text-sm text-gray-700">
            {{ user.profile.nlp_labels?.join(', ') ?? 'Not yet taken' }}
          </p>
        </div>
      </div>

      <WeightPanel :weights="user.profile.weights" />

      <div class="flex gap-3">
        <RouterLink
          to="/recommendations"
          class="flex-1 bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition-colors text-center"
        >
          <p class="font-medium text-gray-800">View Recommendations</p>
          <p class="text-xs text-gray-500 mt-1">Top career matches with SHAP explanations</p>
        </RouterLink>
        <RouterLink
          to="/jobs"
          class="flex-1 bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition-colors text-center"
        >
          <p class="font-medium text-gray-800">Browse Jobs</p>
          <p class="text-xs text-gray-500 mt-1">Live listings matched to your profile</p>
        </RouterLink>
      </div>
    </template>
  </div>
</template>
