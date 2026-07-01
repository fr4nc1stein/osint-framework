<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api/client'

const settings = ref(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.getAiSettings()
    settings.value = data
  } finally {
    loading.value = false
  }
})

const envExample = computed(() => {
  if (!settings.value) return ''
  return [
    '# In your .env file:',
    `AI_PROVIDER=${settings.value.provider}`,
    `AI_MODEL=${settings.value.model}`,
    '',
    '# For Anthropic:',
    'ANTHROPIC_API_KEY=sk-ant-...',
    '',
    '# For OpenAI:',
    '# OPENAI_API_KEY=sk-...',
    '',
    '# For Ollama (local):',
    '# OLLAMA_URL=http://localhost:11434',
  ].join('\n')
})

const modelOptions = computed(() => {
  if (!settings.value) return []
  const p = settings.value.provider
  if (p === 'anthropic') return ['claude-sonnet-4-6', 'claude-opus-4-8', 'claude-haiku-4-5-20251001']
  if (p === 'openai')    return ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
  if (p === 'ollama')    return ['llama3', 'mistral', 'codellama', 'gemma']
  return []
})

const envInstructions = computed(() => {
  if (!settings.value) return {}
  const p = settings.value.provider
  return {
    anthropic: { key: 'ANTHROPIC_API_KEY', model: 'AI_MODEL', provider: 'AI_PROVIDER=anthropic' },
    openai:    { key: 'OPENAI_API_KEY',    model: 'AI_MODEL', provider: 'AI_PROVIDER=openai'    },
    ollama:    { key: '(none needed)',      model: 'AI_MODEL', provider: 'AI_PROVIDER=ollama'    },
  }[p] || {}
})
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="page-header">
      <div>
        <h1 class="page-title">AI Settings</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">Configure the AI analyst provider and model</p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <div v-else-if="settings" class="max-w-2xl space-y-6">
      <!-- Current config -->
      <div class="card p-5">
        <h2 class="font-semibold mb-4" style="color: var(--text-primary)">Current Configuration</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm" style="color: var(--text-secondary)">Provider</span>
            <span class="badge badge-blue capitalize">{{ settings.provider }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm" style="color: var(--text-secondary)">Model</span>
            <span class="text-sm font-mono" style="color: var(--text-primary)">{{ settings.model }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm" style="color: var(--text-secondary)">API Key</span>
            <span class="flex items-center gap-1.5 text-sm"
              :style="settings.has_api_key ? 'color: #6ee7b7' : 'color: #f87171'">
              <span class="h-2 w-2 rounded-full inline-block" :style="settings.has_api_key ? 'background:#10b981' : 'background:#ef4444'"></span>
              {{ settings.has_api_key ? 'Configured' : 'Missing' }}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm" style="color: var(--text-secondary)">Temperature</span>
            <span class="text-sm font-mono" style="color: var(--text-primary)">{{ settings.temperature }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm" style="color: var(--text-secondary)">Max Tokens</span>
            <span class="text-sm font-mono" style="color: var(--text-primary)">{{ settings.max_tokens }}</span>
          </div>
        </div>
      </div>

      <!-- Configuration instructions -->
      <div class="card p-5">
        <h2 class="font-semibold mb-3" style="color: var(--text-primary)">How to Configure</h2>
        <p class="text-sm mb-4" style="color: var(--text-secondary)">
          AI settings are configured via environment variables in your <code class="text-xs px-1 py-0.5 rounded" style="background-color: var(--bg-tertiary)">.env</code> file:
        </p>

        <div class="space-y-4">
          <div>
            <p class="text-xs font-semibold uppercase mb-2" style="color: var(--text-muted)">Provider Options</p>
            <div v-for="(p, name) in { anthropic: 'Recommended — Claude models', openai: 'GPT-4o models', ollama: 'Local models (no API key needed)' }" :key="name"
              class="flex items-center justify-between py-2 border-b last:border-0" style="border-color: var(--border)">
              <div>
                <span class="text-sm font-medium capitalize" style="color: var(--text-primary)">{{ name }}</span>
                <span class="text-xs ml-2" style="color: var(--text-muted)">{{ p }}</span>
              </div>
              <span v-if="settings.provider === name" class="badge badge-green">Active</span>
            </div>
          </div>

          <pre class="text-xs p-4 rounded overflow-x-auto" style="background-color: var(--bg-primary); color: #6ee7b7">{{ envExample }}</pre>
        </div>
      </div>

      <!-- Model reference -->
      <div class="card p-5">
        <h2 class="font-semibold mb-3" style="color: var(--text-primary)">Available Models for {{ settings.provider }}</h2>
        <div class="space-y-2">
          <div v-for="m in modelOptions" :key="m"
            class="flex items-center justify-between py-2 border-b last:border-0" style="border-color: var(--border)">
            <code class="text-xs" style="color: var(--text-primary)">{{ m }}</code>
            <span v-if="m === settings.model" class="badge badge-blue">Current</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
