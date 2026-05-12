<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'

const router = useRouter()

type SurveyType = 'aptitude' | 'personality' | 'open_text'
const currentStep = ref<SurveyType | 'complete'>('aptitude')

// Aptitude state
const aptitudeAnswers = ref<number[]>([])

// Personality (OCEAN) state — five sliders in [0, 1]
const ocean = ref({ O: 0.5, C: 0.5, E: 0.5, A: 0.5, N: 0.5 })
const oceanLabels = { O: 'Openness', C: 'Conscientiousness', E: 'Extraversion', A: 'Agreeableness', N: 'Neuroticism' }

// Open-text state
const openText = ref('')
const nlpProcessing = ref(false)
const nlpSessionId = ref<string | null>(null)

const error = ref('')

async function submitAptitude() {
  error.value = ''
  try {
    const { data } = await api.post('/survey/start', { survey_type: 'aptitude' })
    await api.post('/survey/submit', { session_id: data.session_id, answers: aptitudeAnswers.value })
    currentStep.value = 'personality'
  } catch (e: any) {
    error.value = e.message
  }
}

async function submitPersonality() {
  error.value = ''
  try {
    const { data } = await api.post('/survey/start', { survey_type: 'personality' })
    await api.post('/survey/submit', {
      session_id: data.session_id,
      answers: [ocean.value.O, ocean.value.C, ocean.value.E, ocean.value.A, ocean.value.N],
    })
    currentStep.value = 'open_text'
  } catch (e: any) {
    error.value = e.message
  }
}

async function submitOpenText() {
  error.value = ''
  nlpProcessing.value = true
  try {
    const { data: session } = await api.post('/survey/start', { survey_type: 'open_text' })
    await api.post('/survey/submit-text', {
      session_id: session.session_id,
      response_text: openText.value,
    })
    nlpSessionId.value = session.session_id
    // Poll for NLP completion
    await pollNlpStatus(session.session_id)
    currentStep.value = 'complete'
  } catch (e: any) {
    error.value = e.message
    nlpProcessing.value = false
  }
}

async function pollNlpStatus(sessionId: string) {
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 1000))
    const { data } = await api.get(`/survey/status/${sessionId}`)
    if (data.status === 'done') return
  }
  throw new Error('NLP processing timed out')
}
</script>

<template>
  <div class="max-w-2xl mx-auto py-10 px-4 space-y-6">
    <h1 class="text-2xl font-semibold text-gray-800">Assessment</h1>

    <!-- Step indicators -->
    <div class="flex gap-2 text-xs">
      <span
        v-for="step in ['aptitude', 'personality', 'open_text']"
        :key="step"
        :class="[
          'px-3 py-1 rounded-full',
          currentStep === step ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500',
        ]"
      >
        {{ step === 'aptitude' ? 'Aptitude' : step === 'personality' ? 'Personality' : 'Reflective' }}
      </span>
    </div>

    <!-- Aptitude (placeholder — questions loaded from /survey/start) -->
    <div v-if="currentStep === 'aptitude'" class="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
      <p class="text-sm text-gray-600">Multiple-choice aptitude questions will appear here.</p>
      <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>
      <button @click="submitAptitude" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
        Next →
      </button>
    </div>

    <!-- Personality (OCEAN sliders) -->
    <div v-else-if="currentStep === 'personality'" class="bg-white border border-gray-200 rounded-lg p-6 space-y-5">
      <div v-for="(label, key) in oceanLabels" :key="key" class="space-y-1">
        <div class="flex justify-between text-sm">
          <span class="text-gray-700">{{ label }}</span>
          <span class="text-gray-400">{{ (ocean[key as keyof typeof ocean] * 100).toFixed(0) }}%</span>
        </div>
        <input
          v-model.number="ocean[key as keyof typeof ocean]"
          type="range"
          min="0"
          max="1"
          step="0.01"
          class="w-full accent-blue-600"
        />
      </div>
      <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>
      <button @click="submitPersonality" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
        Next →
      </button>
    </div>

    <!-- Open-text reflective question -->
    <div v-else-if="currentStep === 'open_text'" class="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
      <label class="block text-sm text-gray-700">
        Describe your interests, values, and the kind of work environment you thrive in.
      </label>
      <textarea
        v-model="openText"
        rows="6"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
        placeholder="Write freely…"
      />
      <div v-if="nlpProcessing" class="flex items-center gap-2 text-sm text-blue-600">
        <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
        Analysing your response…
      </div>
      <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>
      <button
        @click="submitOpenText"
        :disabled="nlpProcessing || openText.trim().length < 30"
        class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        Submit
      </button>
    </div>

    <!-- Complete -->
    <div v-else class="bg-white border border-green-200 rounded-lg p-6 text-center space-y-3">
      <p class="text-green-700 font-medium">Assessment complete!</p>
      <RouterLink to="/recommendations" class="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
        View your career matches →
      </RouterLink>
    </div>
  </div>
</template>
