<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

const router = useRouter()

const status    = ref(null)
const dismissed = ref(false)
const importing = ref(false)
const importResult = ref(null)

const DISMISS_KEY = 'osif-setup-dismissed'

onMounted(async () => {
  if (localStorage.getItem(DISMISS_KEY)) {
    dismissed.value = true
    return
  }
  try {
    const { data } = await api.getSetupStatus()
    status.value = data
  } catch {
    // non-fatal — don't block the app
  }
})

function dismiss() {
  dismissed.value = true
  localStorage.setItem(DISMISS_KEY, '1')
}

async function importFromEnv() {
  importing.value = true
  try {
    const { data } = await api.importEnvIntegrations()
    importResult.value = data
    // Refresh status
    const s = await api.getSetupStatus()
    status.value = s.data
  } catch {
    // ignore
  } finally {
    importing.value = false
  }
}

function goToIntegrations() {
  router.push('/integrations')
  dismiss()
}

function goToAi() {
  router.push('/settings/ai')
  dismiss()
}

const show = () =>
  !dismissed.value &&
  status.value &&
  status.value.needs_setup
</script>

<template>
  <Transition name="banner">
    <div v-if="show()"
      class="mx-4 mt-3 mb-0 rounded-lg border px-4 py-3 flex items-start gap-3"
      style="background-color: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.25);">

      <!-- Icon -->
      <svg class="h-5 w-5 shrink-0 mt-0.5" style="color:#3b82f6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/>
      </svg>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium" style="color: var(--text-primary)">
          Welcome to OSIF — finish setting up your integrations
        </p>

        <!-- Import available -->
        <div v-if="status.importable_count > 0 && !importResult" class="mt-1 text-sm" style="color: var(--text-secondary)">
          {{ status.importable_count }} API key{{ status.importable_count > 1 ? 's' : '' }} found in
          <code class="text-xs px-1 rounded" style="background-color: var(--bg-tertiary)">.env</code>
          ({{ status.importable.join(', ') }}) — import them into the DB now.
        </div>

        <!-- Import done -->
        <div v-else-if="importResult" class="mt-1 text-sm" style="color: #6ee7b7">
          ✓ Imported {{ importResult.count }} key{{ importResult.count !== 1 ? 's' : '' }} into the database.
        </div>

        <!-- Nothing in env either -->
        <div v-else class="mt-1 text-sm" style="color: var(--text-secondary)">
          No API keys configured yet. Go to Integrations to add them.
        </div>

        <!-- AI hint -->
        <div v-if="!status.ai_configured_db && !status.ai_configured_env" class="mt-1 text-sm" style="color: var(--text-secondary)">
          AI analysis also needs an API key — configure it in AI Settings.
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-2 mt-2">
          <button v-if="status.importable_count > 0 && !importResult"
            class="btn-primary text-xs px-3 py-1.5"
            :disabled="importing"
            @click="importFromEnv">
            {{ importing ? 'Importing…' : `Import ${status.importable_count} key${status.importable_count > 1 ? 's' : ''} from .env` }}
          </button>
          <button class="btn-secondary text-xs px-3 py-1.5" @click="goToIntegrations">
            Integrations
          </button>
          <button v-if="!status.ai_configured_db" class="btn-secondary text-xs px-3 py-1.5" @click="goToAi">
            AI Settings
          </button>
        </div>
      </div>

      <!-- Dismiss -->
      <button class="btn-ghost p-1 shrink-0" @click="dismiss" title="Dismiss">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>

    </div>
  </Transition>
</template>

<style scoped>
.banner-enter-active, .banner-leave-active { transition: all 0.2s ease; }
.banner-enter-from, .banner-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
