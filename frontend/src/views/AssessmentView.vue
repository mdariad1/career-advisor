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

// ── State ────────────────────────────────────────────────────────────────────

const currentStep = ref<Step>('aptitude')
const error = ref('')
const loading = ref(false)

// Aptitude
const aptitudeSessionId = ref('')
const aptitudeQuestions = ref<Question[]>([])
const aptitudeAnswers = ref<number[]>([])   // -1 = unanswered
const aptitudeResult = ref<{ score: number; correct: number; total: number } | null>(null)

// Personality
const personalitySessionId = ref('')
const personalityQuestions = ref<Question[]>([])
const personalityAnswers = ref<number[]>([])  // Likert 0-4, default 2 (neutral)

// Open text
const openText = ref('')
const nlpProcessing = ref(false)
const nlpSessionId = ref('')

const LIKERT_LABELS = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']

// ── Aptitude ─────────────────────────────────────────────────────────────────

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
  personalityAnswers.value = new Array(data.questions.length).fill(2)  // default neutral
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
    nlpSessionId.value = session.session_id
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
  // Non-fatal: NLP may finish async; user can still proceed
}

// Kick off aptitude questions immediately on mount
startAptitude()
</script>

<template>
  <div class="max-w-2xl mx-auto py-10 px-4 space-y-6">
    <h1 class="text-2xl font-semibold text-gray-800">Assessment</h1>

    <!-- Step indicators -->
    <div class="flex gap-2 text-xs">
      <span
        v-for="step in (['aptitude', 'personality', 'open_text'] as Step[])"
        :key="step"
        :class="[
          'px-3 py-1 rounded-full',
          currentStep === step ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500',
        ]"
      >
        {{ step === 'aptitude' ? 'Aptitude' : step === 'personality' ? 'Personality' : 'Reflective' }}
      </span>
    </div>

    <!-- Loading spinner (fetching questions) -->
    <div v-if="loading && aptitudeQuestions.length === 0 && currentStep === 'aptitude'"
         class="text-gray-400 text-sm">
      Loading questions…
    </div>

    <!-- ── Aptitude ─────────────────────────────────────────────────────── -->
    <div v-else-if="currentStep === 'aptitude'"
         class="bg-white border border-gray-200 rounded-lg p-6 space-y-6">

      <p class="text-sm text-gray-500">
        {{ aptitudeQuestions.length }} multiple-choice questions — select one answer per question.
      </p>

      <div
        v-for="(q, qi) in aptitudeQuestions"
        :key="q.id"
        class="space-y-2"
      >
        <p class="text-sm font-medium text-gray-800">{{ qi + 1 }}. {{ q.question }}</p>
        <div class="space-y-1 pl-2">
          <label
            v-for="(choice, ci) in q.choices"
            :key="ci"
            :class="[
              'flex items-center gap-2 text-sm px-3 py-2 rounded-lg cursor-pointer',
              aptitudeAnswers[qi] === ci
                ? 'bg-blue-50 border border-blue-300 text-blue-800'
                : 'border border-gray-100 text-gray-700 hover:bg-gray-50',
            ]"
          >
            <input
              type="radio"
              :name="`aptitude-${qi}`"
              :value="ci"
              v-model="aptitudeAnswers[qi]"
              class="accent-blue-600"
            />
            {{ choice }}
          </label>
        </div>
      </div>

      <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>

      <button
        @click="submitAptitude"
        :disabled="loading"
        class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'Submitting…' : 'Next →' }}
      </button>
    </div>

    <!-- ── Personality ──────────────────────────────────────────────────── -->
    <div v-else-if="currentStep === 'personality'"
         class="bg-white border border-gray-200 rounded-lg p-6 space-y-5">

      <p class="text-sm text-gray-500">
        Rate how well each statement describes you on a scale from
        <em>Strongly disagree</em> to <em>Strongly agree</em>.
      </p>

      <div
        v-for="(q, qi) in personalityQuestions"
        :key="q.id"
        class="space-y-2"
      >
        <p class="text-sm font-medium text-gray-800">{{ qi + 1 }}. {{ q.question }}</p>
        <div class="flex gap-1">
          <button
            v-for="(label, val) in LIKERT_LABELS"
            :key="val"
            @click="personalityAnswers[qi] = val"
            :title="label"
            :class="[
              'flex-1 py-2 rounded text-xs border transition-colors',
              personalityAnswers[qi] === val
                ? 'bg-blue-600 border-blue-600 text-white font-medium'
                : 'border-gray-200 text-gray-500 hover:border-blue-300 hover:text-blue-600',
            ]"
          >
            {{ val }}
          </button>
        </div>
        <div class="flex justify-between text-xs text-gray-400 px-0.5">
          <span>Strongly disagree</span>
          <span>Strongly agree</span>
        </div>
      </div>

      <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>

      <button
        @click="submitPersonality"
        :disabled="loading"
        class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'Submitting…' : 'Next →' }}
      </button>
    </div>

    <!-- ── Open-text ────────────────────────────────────────────────────── -->
    <div v-else-if="currentStep === 'open_text'"
         class="bg-white border border-gray-200 rounded-lg p-6 space-y-4">

      <label class="block text-sm text-gray-700 font-medium">
        Describe your interests, values, and the kind of work environment you thrive in.
      </label>
      <p class="text-xs text-gray-400">Write at least 30 characters. Your response is analysed by our NLP model to match thematic career labels.</p>

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
        class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        Submit
      </button>
    </div>

    <!-- ── Complete ─────────────────────────────────────────────────────── -->
    <div v-else class="bg-white border border-green-200 rounded-lg p-6 text-center space-y-3">
      <p class="text-green-700 font-medium text-lg">Assessment complete!</p>
      <p v-if="aptitudeResult" class="text-sm text-gray-600">
        Aptitude: {{ aptitudeResult.correct }}/{{ aptitudeResult.total }}
        ({{ (aptitudeResult.score * 100).toFixed(0) }}%)
      </p>
      <RouterLink
        to="/recommendations"
        class="inline-block bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700"
      >
        View your career matches →
      </RouterLink>
    </div>
  </div>
</template>
