<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { api } from '../api/client'
import { useCasesStore } from '../stores/cases'

const casesStore = useCasesStore()

const messages = ref([
  { role: 'assistant', content: 'Hello! I\'m your OSINT analyst. Ask me to summarize findings, suggest next steps, or generate insights from your investigations.' }
])
const input = ref('')
const loading = ref(false)
const aiReady = ref(false)
const selectedCaseId = ref('')
const messagesEl = ref(null)

const suggestions = [
  'Summarize this investigation',
  'What are the key indicators?',
  'Suggest next investigation steps',
  'Identify potential threat actors',
]

onMounted(async () => {
  try {
    const { data } = await api.getAiSettings()
    aiReady.value = data.has_api_key
  } catch {}
  await casesStore.fetchCases()
})

async function scrollBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

async function send(text) {
  const msg = (text || input.value).trim()
  if (!msg || loading.value) return
  input.value = ''

  messages.value.push({ role: 'user', content: msg })
  await scrollBottom()

  loading.value = true
  try {
    const { data } = await api.analyzeWithAi({
      prompt: msg,
      case_id: selectedCaseId.value || undefined,
      context_type: 'case',
    })
    messages.value.push({ role: 'assistant', content: data.response })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `Error: ${e.response?.data?.detail || e.message}` })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}
</script>

<template>
  <div class="h-full flex flex-col p-6">
    <div class="page-header shrink-0">
      <div>
        <h1 class="page-title">AI Analyst</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">Chat with AI about your investigations</p>
      </div>

      <!-- Case selector -->
      <select v-model="selectedCaseId" class="input w-56">
        <option value="">No case context</option>
        <option v-for="c in casesStore.cases" :key="c.id" :value="c.id">{{ c.title }}</option>
      </select>
    </div>

    <!-- Not configured -->
    <div v-if="!aiReady" class="card p-6 text-center mb-4">
      <p class="font-medium mb-2" style="color: var(--text-primary)">AI not configured</p>
      <p class="text-sm mb-4" style="color: var(--text-secondary)">
        Set <code class="text-xs px-1 py-0.5 rounded" style="background-color: var(--bg-tertiary)">ANTHROPIC_API_KEY</code> (or OpenAI/Ollama) in your <code class="text-xs px-1 py-0.5 rounded" style="background-color: var(--bg-tertiary)">.env</code> file and restart the backend.
      </p>
      <RouterLink to="/settings/ai" class="btn-primary">Go to AI Settings</RouterLink>
    </div>

    <!-- Messages -->
    <div ref="messagesEl" class="flex-1 overflow-y-auto space-y-4 mb-4 min-h-0">
      <div v-for="(m, i) in messages" :key="i"
        class="flex"
        :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div class="max-w-[80%] rounded-2xl px-4 py-3 text-sm"
          :style="m.role === 'user'
            ? 'background-color: var(--accent); color: #fff'
            : 'background-color: var(--card-bg); color: var(--text-primary); border: 1px solid var(--border)'"
        >
          <p class="whitespace-pre-wrap">{{ m.content }}</p>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="loading" class="flex justify-start">
        <div class="card px-4 py-3 flex gap-1.5 items-center">
          <span v-for="n in 3" :key="n" class="h-2 w-2 rounded-full bg-blue-400 animate-bounce" :style="`animation-delay: ${(n-1)*0.15}s`"></span>
        </div>
      </div>
    </div>

    <!-- Suggestions -->
    <div v-if="messages.length <= 1" class="flex flex-wrap gap-2 mb-3 shrink-0">
      <button v-for="s in suggestions" :key="s"
        class="badge badge-blue cursor-pointer hover:bg-blue-500/30 transition-all text-xs px-3 py-1.5"
        @click="send(s)"
      >
        {{ s }}
      </button>
    </div>

    <!-- Input -->
    <div class="flex gap-3 shrink-0">
      <textarea
        v-model="input"
        class="input flex-1 resize-none h-12 py-3"
        :disabled="!aiReady || loading"
        placeholder="Ask about your investigation…"
        @keydown.enter.prevent="send()"
      />
      <button class="btn-primary px-5" :disabled="!aiReady || loading || !input.trim()" @click="send()">
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
  </div>
</template>
