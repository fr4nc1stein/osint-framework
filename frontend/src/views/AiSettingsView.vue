<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api/client'

const settings  = ref(null)
const providers = ref([])
const loading   = ref(false)
const saving    = ref(false)
const testing   = ref(false)
const error     = ref(null)
const showKey   = ref(false)

const form = ref({
  provider:    'anthropic',
  model:       'claude-sonnet-4-6',
  api_key:     '',
  base_url:    '',
  temperature: 0.3,
  max_tokens:  2048,
})

const PROVIDER_MODELS = {
  anthropic: ['claude-sonnet-4-6', 'claude-opus-4-8', 'claude-haiku-4-5-20251001'],
  openai:    ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
  ollama:    ['llama3', 'mistral', 'codellama', 'gemma'],
}

const modelOptions = computed(() => PROVIDER_MODELS[form.value.provider] || [])
const needsKey     = computed(() => form.value.provider !== 'ollama')
const isOllama     = computed(() => form.value.provider === 'ollama')

onMounted(async () => {
  loading.value = true
  try {
    const [s, p] = await Promise.all([api.getAiSettings(), api.getAiProviders()])
    settings.value  = s.data
    providers.value = p.data
    // Populate form from current settings
    form.value = {
      provider:    s.data.provider,
      model:       s.data.model,
      api_key:     '',
      base_url:    s.data.base_url || '',
      temperature: s.data.temperature,
      max_tokens:  s.data.max_tokens,
    }
  } finally {
    loading.value = false
  }
})

// Reset model to provider default when provider changes
watch(() => form.value.provider, (p) => {
  const models = PROVIDER_MODELS[p] || []
  if (!models.includes(form.value.model)) {
    form.value.model = models[0] || ''
  }
})

async function save() {
  saving.value = true
  error.value  = null
  try {
    const payload = { ...form.value }
    if (!payload.api_key.trim()) delete payload.api_key   // keep existing key
    if (!payload.base_url.trim()) delete payload.base_url
    const { data } = await api.saveAiSettings(payload)
    settings.value = data
    form.value.api_key = ''
    showKey.value = false
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  error.value   = null
  try {
    const { data } = await api.testAiSettings()
    settings.value = { ...settings.value, last_test_status: data.status, last_test_message: data.message, last_tested_at: new Date().toISOString() }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    testing.value = false
  }
}

function fmtDate(d) {
  if (!d) return null
  return new Date(d).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="page-header">
      <div>
        <h1 class="page-title">AI Settings</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">Configure the AI analyst provider. Keys are encrypted at rest.</p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <div v-else class="max-w-2xl space-y-5">

      <!-- Status card -->
      <div v-if="settings" class="card p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-semibold" style="color: var(--text-primary)">Current Configuration</h2>
          <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
            :style="settings.source === 'db'
              ? 'background:rgba(16,185,129,0.15);color:#6ee7b7'
              : 'background:rgba(245,158,11,0.15);color:#fcd34d'">
            <span class="h-1.5 w-1.5 rounded-full inline-block"
              :style="settings.source === 'db' ? 'background:#10b981' : 'background:#f59e0b'"></span>
            {{ settings.source === 'db' ? 'Saved in DB' : 'From .env' }}
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 text-sm mb-4">
          <div>
            <span style="color:var(--text-muted)">Provider</span>
            <p class="font-medium capitalize mt-0.5" style="color:var(--text-primary)">{{ settings.provider }}</p>
          </div>
          <div>
            <span style="color:var(--text-muted)">Model</span>
            <p class="font-mono text-xs mt-0.5" style="color:var(--text-primary)">{{ settings.model }}</p>
          </div>
          <div>
            <span style="color:var(--text-muted)">API Key</span>
            <p class="mt-0.5 flex items-center gap-1.5" :style="settings.has_api_key ? 'color:#6ee7b7' : 'color:#f87171'">
              <span class="h-2 w-2 rounded-full inline-block" :style="settings.has_api_key ? 'background:#10b981' : 'background:#ef4444'"></span>
              {{ settings.masked_hint || (settings.has_api_key ? 'Configured' : 'Missing') }}
            </p>
          </div>
          <div>
            <span style="color:var(--text-muted)">Temperature / Max tokens</span>
            <p class="font-mono text-xs mt-0.5" style="color:var(--text-primary)">{{ settings.temperature }} / {{ settings.max_tokens }}</p>
          </div>
        </div>

        <!-- Test result -->
        <div v-if="settings.last_test_status" class="text-xs px-3 py-2 rounded flex items-center gap-2 mb-3"
          :style="settings.last_test_status === 'ok'
            ? 'background:rgba(16,185,129,0.1);color:#6ee7b7'
            : 'background:rgba(239,68,68,0.1);color:#fca5a5'">
          <span>{{ settings.last_test_status === 'ok' ? '✓' : '✗' }}</span>
          <span class="flex-1">{{ settings.last_test_message }}</span>
          <span style="color:var(--text-muted)">{{ fmtDate(settings.last_tested_at) }}</span>
        </div>

        <button class="btn-secondary text-sm w-full" :disabled="!settings.has_api_key || testing" @click="testConnection">
          {{ testing ? 'Testing…' : 'Test Connection' }}
        </button>
      </div>

      <!-- Edit form -->
      <div class="card p-5 space-y-4">
        <h2 class="font-semibold" style="color: var(--text-primary)">Configure Provider</h2>

        <div v-if="error" class="text-sm px-3 py-2 rounded" style="background:rgba(239,68,68,0.12);color:#f87171">{{ error }}</div>

        <!-- Provider selector -->
        <div>
          <label class="form-label">Provider</label>
          <div class="grid grid-cols-3 gap-2">
            <button v-for="p in ['anthropic','openai','ollama']" :key="p"
              class="py-2 px-3 rounded-lg border text-sm font-medium transition-all capitalize"
              :style="form.provider === p
                ? 'background:var(--accent);color:#fff;border-color:var(--accent)'
                : 'background:var(--bg-secondary);color:var(--text-secondary);border-color:var(--border)'"
              @click="form.provider = p">
              {{ p }}
            </button>
          </div>
        </div>

        <!-- Model -->
        <div>
          <label class="form-label">Model</label>
          <select v-model="form.model" class="input">
            <option v-for="m in modelOptions" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>

        <!-- API key (not for Ollama) -->
        <div v-if="needsKey">
          <label class="form-label">API Key</label>
          <div class="relative">
            <input
              v-model="form.api_key"
              :type="showKey ? 'text' : 'password'"
              class="input pr-8"
              :placeholder="settings?.has_api_key && settings?.provider === form.provider
                ? 'Enter new key to replace existing…'
                : 'Paste API key…'"
            />
            <button class="absolute right-2 top-1/2 -translate-y-1/2 btn-ghost p-0"
              @click="showKey = !showKey">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path v-if="!showKey" d="M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                <path v-else d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
              </svg>
            </button>
          </div>
          <p class="text-xs mt-1" style="color:var(--text-muted)">Leave blank to keep the existing key.</p>
        </div>

        <!-- Base URL (Ollama) -->
        <div v-if="isOllama">
          <label class="form-label">Ollama Base URL</label>
          <input v-model="form.base_url" class="input" placeholder="http://localhost:11434" />
        </div>

        <!-- Temperature + max tokens -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="form-label">Temperature <span class="font-mono">{{ form.temperature }}</span></label>
            <input v-model.number="form.temperature" type="range" min="0" max="1" step="0.05"
              class="w-full accent-blue-500" />
          </div>
          <div>
            <label class="form-label">Max Tokens</label>
            <input v-model.number="form.max_tokens" type="number" min="256" max="8192" step="256" class="input" />
          </div>
        </div>

        <button class="btn-primary w-full" :disabled="saving" @click="save">
          {{ saving ? 'Saving…' : 'Save Settings' }}
        </button>
      </div>

    </div>
  </div>
</template>
