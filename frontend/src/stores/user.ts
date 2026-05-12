import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'

export interface WeightVector {
  aptitude: number
  personality_fit: number
  nlp_similarity: number
  market_demand: number
}

export interface UserProfile {
  user_id: string
  email: string
  full_name: string
  aptitude_score: number | null
  ocean_vector: number[] | null
  nlp_labels: string[] | null
  weights: WeightVector
}

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile | null>(null)
  const loading = ref(false)

  async function fetchProfile() {
    loading.value = true
    try {
      const { data } = await api.get('/profile/')
      profile.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchWeights() {
    const { data } = await api.get('/profile/weights')
    if (profile.value) profile.value.weights = data
    return data as WeightVector
  }

  function clearProfile() {
    profile.value = null
  }

  return { profile, loading, fetchProfile, fetchWeights, clearProfile }
})
