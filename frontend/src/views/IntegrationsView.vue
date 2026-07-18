<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'

const integrations = ref([])
const loading = ref(false)
const savingProvider = ref(null)
const testingProvider = ref(null)
const importingEnv = ref(false)
const importResult = ref(null)
const keyInputs = ref({})
const showKey = ref({})

const categoryColors = {
  recon:  'badge-blue',
  threat: 'badge-red',
  email:  'badge-amber',
  breach: 'badge-purple',
}

onMounted(() => loadIntegrations())

async function loadIntegrations() {
  loading.value = true
  try {
    const { data } = await api.getIntegrations()
    integrations.value = data
    data.forEach(itg => { keyInputs.value[itg.provider] = '' })
  } finally {
    loading.value = false
  }
}

async function saveKey(provider) {
  const key = keyInputs.value[provider]?.trim()
  if (!key) return
  savingProvider.value = provider
  try {
    const { data } = await api.saveIntegration(provider, { api_key: key, enabled: true })
    const idx = integrations.value.findIndex(i => i.provider === provider)
    if (idx !== -1) integrations.value[idx] = data
    keyInputs.value[provider] = ''
    showKey.value[provider] = false
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to save key')
  } finally {
    savingProvider.value = null
  }
}

async function removeKey(provider) {
  if (!confirm('Remove stored key for ' + provider + '?')) return
  try {
    await api.deleteIntegration(provider)
    await loadIntegrations()
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to remove key')
  }
}

async function testProvider(provider) {
  testingProvider.value = provider
  try {
    const { data } = await api.testIntegration(provider)
    const idx = integrations.value.findIndex(i => i.provider === provider)
    if (idx !== -1) {
      integrations.value[idx].last_test_status = data.status
      integrations.value[idx].last_test_message = data.message
      integrations.value[idx].last_tested_at = new Date().toISOString()
    }
  } catch (e) {
    alert(e.response?.data?.detail || 'Test failed')
  } finally {
    testingProvider.value = null
  }
}

async function importFromEnv() {
  importingEnv.value = true
  importResult.value = null
  try {
    const { data } = await api.importEnvIntegrations()
    importResult.value = data
    await loadIntegrations()
  } catch (e) {
    alert(e.response?.data?.detail || 'Import failed')
  } finally {
    importingEnv.value = false
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
        <h1 class="page-title">Integrations</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">
          Configure API keys. Keys are encrypted at rest and never returned in plain text.
        </p>
      </div>
      <button class="btn-secondary flex items-center gap-2 text-sm" :disabled="importingEnv" @click="importFromEnv">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
        </svg>
        {{ importingEnv ? 'Importing…' : 'Import from .env' }}
      </button>
    </div>

    <div v-if="importResult" class="mb-5 px-4 py-3 rounded-lg text-sm flex items-center justify-between"
      style="background-color:rgba(16,185,129,0.1);color:#6ee7b7;border:1px solid rgba(16,185,129,0.2)">
      <span>Imported {{ importResult.count }} key(s): {{ importResult.imported.join(', ') || 'none new' }}</span>
      <button class="btn-ghost text-xs" @click="importResult = null">✕</button>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="itg in integrations" :key="itg.provider" class="card p-5 flex flex-col gap-3">

        <!-- Header row -->
        <div class="flex items-start justify-between">
          <div>
            <h3 class="font-semibold" style="color:var(--text-primary)">{{ itg.display_name }}</h3>
            <span class="badge text-[10px] mt-1" :class="categoryColors[itg.category] || 'badge-slate'">{{ itg.category }}</span>
          </div>
          <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium shrink-0"
            :style="itg.has_key
              ? (itg.source === 'env_fallback' ? 'background:rgba(245,158,11,0.15);color:#fcd34d' : 'background:rgba(16,185,129,0.15);color:#6ee7b7')
              : 'background:rgba(100,116,139,0.15);color:#94a3b8'">
            <span class="h-1.5 w-1.5 rounded-full inline-block"
              :style="itg.has_key ? (itg.source === 'env_fallback' ? 'background:#f59e0b' : 'background:#10b981') : 'background:#64748b'"></span>
            {{ itg.source === 'db' ? 'Configured' : itg.source === 'env_fallback' ? 'From .env' : 'Not set' }}
          </div>
        </div>

        <p class="text-sm" style="color:var(--text-secondary)">{{ itg.description }}</p>

        <!-- Current key hint -->
        <div v-if="itg.has_key" class="flex items-center justify-between text-xs px-2 py-1.5 rounded"
          style="background-color:var(--bg-primary)">
          <span class="font-mono" style="color:var(--text-muted)">{{ itg.masked_hint || '••••••••' }}</span>
          <button v-if="itg.source === 'db'" class="text-red-400 hover:text-red-300" @click="removeKey(itg.provider)">Remove</button>
          <span v-else class="text-[10px]" style="color:var(--text-muted)">.env</span>
        </div>

        <!-- Test result -->
        <div v-if="itg.last_test_status" class="text-xs px-2 py-1.5 rounded flex items-center gap-2"
          :style="itg.last_test_status === 'ok'
            ? 'background:rgba(16,185,129,0.1);color:#6ee7b7'
            : 'background:rgba(239,68,68,0.1);color:#fca5a5'">
          <span>{{ itg.last_test_status === 'ok' ? '✓' : '✗' }}</span>
          <span class="flex-1">{{ itg.last_test_message }}</span>
          <span style="color:var(--text-muted)">{{ fmtDate(itg.last_tested_at) }}</span>
        </div>

        <!-- Key input -->
        <div class="flex gap-2">
          <div class="relative flex-1">
            <input
              v-model="keyInputs[itg.provider]"
              :type="showKey[itg.provider] ? 'text' : 'password'"
              class="input pr-8 text-sm"
              :placeholder="itg.has_key ? 'Enter new key to replace…' : 'Paste API key…'"
              @keyup.enter="saveKey(itg.provider)"
            />
            <button class="absolute right-2 top-1/2 -translate-y-1/2 btn-ghost p-0"
              @click="showKey[itg.provider] = !showKey[itg.provider]">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path v-if="!showKey[itg.provider]" d="M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                <path v-else d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
              </svg>
            </button>
          </div>
          <button class="btn-primary text-sm px-3"
            :disabled="!keyInputs[itg.provider]?.trim() || savingProvider === itg.provider"
            @click="saveKey(itg.provider)">
            {{ savingProvider === itg.provider ? '…' : 'Save' }}
          </button>
        </div>

        <button class="btn-secondary text-xs w-full"
          :disabled="!itg.has_key || testingProvider === itg.provider"
          @click="testProvider(itg.provider)">
          {{ testingProvider === itg.provider ? 'Testing…' : 'Test Connection' }}
        </button>

      </div>
    </div>
  </div>
</template>
