<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'

const integrations = ref([])
const loading = ref(false)

const categoryColors = {
  recon:  'badge-blue',
  threat: 'badge-red',
  email:  'badge-amber',
  breach: 'badge-purple',
}

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.getIntegrations()
    integrations.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="page-header">
      <div>
        <h1 class="page-title">Integrations</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">
          External API connections. Configure keys in your <code class="text-xs px-1 py-0.5 rounded" style="background-color: var(--bg-tertiary)">.env</code> file.
        </p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="itg in integrations" :key="itg.id" class="card p-5">
        <div class="flex items-start justify-between mb-3">
          <div>
            <h3 class="font-semibold" style="color: var(--text-primary)">{{ itg.name }}</h3>
            <span class="badge text-[10px] mt-1" :class="categoryColors[itg.category] || 'badge-slate'">{{ itg.category }}</span>
          </div>
          <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
            :style="itg.is_configured
              ? 'background-color: rgba(16,185,129,0.15); color: #6ee7b7'
              : 'background-color: rgba(100,116,139,0.15); color: #94a3b8'">
            <span class="h-1.5 w-1.5 rounded-full inline-block"
              :style="itg.is_configured ? 'background:#10b981' : 'background:#64748b'"></span>
            {{ itg.is_configured ? 'Configured' : 'Not set' }}
          </div>
        </div>

        <p class="text-sm mb-4" style="color: var(--text-secondary)">{{ itg.description }}</p>

        <div class="text-xs font-mono px-2 py-1.5 rounded" style="background-color: var(--bg-primary); color: var(--text-muted)">
          {{ itg.env_var }}
        </div>

        <div class="mt-3 flex gap-2">
          <button class="btn-secondary text-xs px-3 py-1.5 w-full opacity-50 cursor-not-allowed" disabled title="Configuration via UI coming in a future release">
            Configure
          </button>
          <button class="btn-ghost text-xs opacity-50 cursor-not-allowed" disabled title="Coming soon">
            Test
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
