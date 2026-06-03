<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'

const router = useRouter()

type Step = 'aptitude' | 'personality' | 'open_text' | 'complete'

interface Question {
  id: string
  question: string
  choices: string[]
  survey_type: string
  grade?: number
}

// ── State ─────────────────────────────────────────────────────────────────────

const currentStep = ref<Step>('aptitude')
const error = ref('')
const loading = ref(false)

// Aptitude
const aptitudeSessionId = ref('')
const aptitudeQuestions = ref<Question[]>([])
const aptitudeAnswers = ref<number[]>([])
const aptitudeResult = ref<{ score: number; correct: number; total: number } | null>(null)

// Personality
const personalitySessionId = ref('')
const personalityQuestions = ref<Question[]>([])
const personalityAnswers = ref<number[]>([])

// Open text
const openText = ref('')
const nlpProcessing = ref(false)

const LIKERT_LABELS = ['SD', 'D', 'N', 'A', 'SA']
const LIKERT_FULL = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']

// ── Aptitude ──────────────────────────────────────────────────────────────────

async function startAptitude() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.post('/survey/start', { survey_type: 'aptitude' })
    aptitudeSessionId.value = data.session_id
    aptitudeQuestions.value = data.questions
    aptitudeAnswers.value = new Array(data.questions.length).fill(-1)
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function submitAptitude() {
  if (aptitudeAnswers.value.some((a) => a === -1)) {
    error.value = 'Please answer all questions before continuing.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.post('/survey/submit', {
      session_id: aptitudeSessionId.value,
      answers: aptitudeAnswers.value,
    })
    aptitudeResult.value = { score: data.score, correct: data.correct, total: data.total }
    await startPersonality()
    currentStep.value = 'personality'
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// ── Personality ───────────────────────────────────────────────────────────────

async function startPersonality() {
  const { data } = await api.post('/survey/start', { survey_type: 'personality' })
  personalitySessionId.value = data.session_id
  personalityQuestions.value = data.questions
  personalityAnswers.value = new Array(data.questions.length).fill(2)
}

async function submitPersonality() {
  loading.value = true
  error.value = ''
  try {
    await api.post('/survey/submit', {
      session_id: personalitySessionId.value,
      answers: personalityAnswers.value,
    })
    currentStep.value = 'open_text'
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// ── Open text ─────────────────────────────────────────────────────────────────

async function submitOpenText() {
  error.value = ''
  nlpProcessing.value = true
  try {
    const { data: session } = await api.post('/survey/start', { survey_type: 'open_text' })
    await api.post('/survey/submit-text', {
      session_id: session.session_id,
      response_text: openText.value,
    })
    await pollNlpStatus(session.session_id)
    currentStep.value = 'complete'
  } catch (e: any) {
    error.value = e.message
  } finally {
    nlpProcessing.value = false
  }
}

async function pollNlpStatus(sessionId: string) {
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 1000))
    const { data } = await api.get(`/survey/status/${sessionId}`)
    if (data.status === 'done') return
  }
}

const answeredCount = () => aptitudeAnswers.value.filter((a) => a !== -1).length

startAptitude()
</script>

<template>
  <div class="max-w-2xl mx-auto py-10 px-6 space-y-6">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold text-neutral-100">Assessment</h1>
      <div class="flex gap-1.5">
        <span
          v-for="(step, i) in ['aptitude', 'personality', 'open_text']"
          :key="step"
          :class="[
            'text-xs px-3 py-1 rounded-full border transition-colors',
            currentStep === step
              ? 'bg-indigo-600 border-indigo-600 text-white'
              : 'border-neutral-800 text-neutral-600',
          ]"
        >
          {{ i === 0 ? 'Aptitude' : i === 1 ? 'Personality' : 'Reflective' }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && aptitudeQuestions.length === 0 && currentStep === 'aptitude'"
         class="text-neutral-600 text-sm py-8 text-center">
      Loading questions…
    </div>

    <!-- ── Aptitude ─────────────────────────────────────────────────────────── -->
    <div v-else-if="currentStep === 'aptitude'" class="space-y-5">
      <div class="flex items-center justify-between text-xs text-neutral-600">
        <span>{{ aptitudeQuestions.length }} questions</span>
        <span>{{ answeredCount() }} / {{ aptitudeQuestions.length }} answered</span>
      </div>

      <div
        v-for="(q, qi) in aptitudeQuestions"
        :key="q.id"
        class="bg-neutral-900 border border-neutral-800 rounded-lg p-4 space-y-3"
      >
        <p class="text-sm text-neutral-200 leading-relaxed">
          <span class="text-neutral-600 mr-1.5">{{ qi + 1 }}.</span>{{ q.question }}
        </p>
        <div class="space-y-1.5">
          <label
            v-for="(choice, ci) in q.choices"
            :key="ci"
            :class="[
              'flex items-center gap-2.5 text-sm px-3 py-2 rounded-lg cursor-pointer border transition-colors',
              aptitudeAnswers[qi] === ci
                ? 'bg-indigo-950 border-indigo-700 text-indigo-200'
                : 'border-neutral-800 text-neutral-400 hover:border-neutral-700 hover:text-neutral-300',
            ]"
          >
            <input
              type="radio"
              :name="`apt-${qi}`"
              :value="ci"
              v-model="aptitudeAnswers[qi]"
              class="accent-indigo-500 shrink-0"
            />
            {{ choice }}
          </label>
        </div>
      </div>

      <p v-if="error" class="text-red-400 text-xs">{{ error }}</p>

      <button
        @click="submitAptitude"
        :disabled="loading"
        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
      >
        {{ loading ? 'Submitting…' : 'Continue →' }}
      </button>
    </div>

    <!-- ── Personality ─────────────────────────────────────────────────────── -->
    <div v-else-if="currentStep === 'personality'" class="space-y-4">
      <p class="text-xs text-neutral-600">
        Rate how well each statement describes you — 0 (strongly disagree) to 4 (strongly agree).
      </p>

      <div
        v-for="(q, qi) in personalityQuestions"
        :key="q.id"
        class="bg-neutral-900 border border-neutral-800 rounded-lg p-4 space-y-3"
      >
        <p class="text-sm text-neutral-200 leading-relaxed">
          <span class="text-neutral-600 mr-1.5">{{ qi + 1 }}.</span>{{ q.question }}
        </p>
        <div class="flex gap-1.5">
          <button
            v-for="(label, val) in LIKERT_LABELS"
            :key="val"
            @click="personalityAnswers[qi] = val"
            :title="LIKERT_FULL[val]"
            :class="[
              'flex-1 py-1.5 rounded text-xs border transition-colors',
              personalityAnswers[qi] === val
                ? 'bg-indigo-600 border-indigo-600 text-white'
                : 'border-neutral-800 text-neutral-600 hover:border-neutral-700 hover:text-neutral-400',
            ]"
          >
            {{ label }}
          </button>
        </div>
      </div>

      <p v-if="error" class="text-red-400 text-xs">{{ error }}</p>

      <button
        @click="submitPersonality"
        :disabled="loading"
        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
      >
        {{ loading ? 'Submitting…' : 'Continue →' }}
      </button>
    </div>

    <!-- ── Open text ───────────────────────────────────────────────────────── -->
    <div v-else-if="currentStep === 'open_text'"
         class="bg-neutral-900 border border-neutral-800 rounded-lg p-5 space-y-4">
      <div>
        <p class="text-sm font-medium text-neutral-200">Reflective question</p>
        <p class="text-xs text-neutral-500 mt-1">
          Describe your interests, values, and the kind of work environment you thrive in.
          Your response is analysed by the NLP model to produce thematic career labels.
        </p>
      </div>

      <textarea
        v-model="openText"
        rows="6"
        class="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-neutral-100 placeholder-neutral-700 resize-none focus:outline-none focus:border-indigo-600 transition-colors"
        placeholder="Write freely… (minimum 30 characters)"
      />

      <div v-if="nlpProcessing" class="flex items-center gap-2 text-sm text-indigo-400">
        <svg class="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
        Analysing your response…
      </div>

      <p v-if="error" class="text-red-400 text-xs">{{ error }}</p>

      <button
        @click="submitOpenText"
        :disabled="nlpProcessing || openText.trim().length < 30"
        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
      >
        Submit
      </button>
    </div>

    <!-- ── Complete ────────────────────────────────────────────────────────── -->
    <div v-else class="bg-neutral-900 border border-neutral-800 rounded-lg p-6 text-center space-y-4">
      <p class="text-neutral-100 font-medium">Assessment complete</p>
      <p v-if="aptitudeResult" class="text-sm text-neutral-500">
        Aptitude: {{ aptitudeResult.correct }}/{{ aptitudeResult.total }}
        ({{ (aptitudeResult.score * 100).toFixed(0) }}%)
      </p>
      <RouterLink
        to="/recommendations"
        class="inline-block bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
      >
        View career matches →
      </RouterLink>
    </div>

  </div>
</template>
