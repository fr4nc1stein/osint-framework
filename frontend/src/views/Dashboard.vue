<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useModulesStore } from '../stores/modules'
import CreateScanModal from '../components/CreateScanModal.vue'

const router = useRouter()
const modulesStore = useModulesStore()

const stats = ref(null)
const loading = ref(false)
const showCreateModal = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const [statsRes] = await Promise.all([
      api.getStats(),
      modulesStore.fetchModules(),
    ])
    stats.value = statsRes.data
  } finally {
    loading.value = false
  }
})

function fmtDate(d) {
  const diff = Date.now() - new Date(d).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

const statusBadge = {
  queued:    'badge-slate',
  running:   'badge-blue',
  completed: 'badge-green',
  partial:   'badge-amber',
  failed:    'badge-red',
  error:     'badge-red',
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">OSIF v2.0 — Open Source Intelligence Framework</p>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="showCreateModal = true">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        New Scan
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <template v-else-if="stats">
      <!-- Stats cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="card p-5 cursor-pointer hover:border-blue-500/30 transition-all" @click="router.push('/cases')">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Total Cases</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary)">{{ stats.cases.total }}</p>
          <p class="text-xs mt-1" style="color: var(--text-secondary)">{{ stats.cases.active }} active · {{ stats.cases.open }} open</p>
        </div>
        <div class="card p-5">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Total Scans</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary)">{{ stats.scans.total }}</p>
          <p class="text-xs mt-1" style="color: var(--text-secondary)">{{ stats.scans.running }} running · {{ stats.scans.completed }} done</p>
        </div>
        <div class="card p-5">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Indicators</p>
          <p class="text-3xl font-bold text-emerald-400">{{ stats.indicators }}</p>
          <p class="text-xs mt-1" style="color: var(--text-secondary)">Graph nodes discovered</p>
        </div>
        <div class="card p-5">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Modules</p>
          <p class="text-3xl font-bold text-purple-400">{{ modulesStore.modules.length }}</p>
          <p class="text-xs mt-1" style="color: var(--text-secondary)">OSINT modules loaded</p>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <!-- Recent Cases -->
        <div class="card">
          <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color: var(--border)">
            <h2 class="font-semibold" style="color: var(--text-primary)">Recent Cases</h2>
            <RouterLink to="/cases" class="text-xs btn-ghost">View all →</RouterLink>
          </div>
          <div v-if="stats.recent_cases.length === 0" class="p-8 text-center" style="color: var(--text-muted)">
            No cases yet. <RouterLink to="/cases" class="text-blue-400 hover:underline">Create one</RouterLink>
          </div>
          <div v-else class="divide-y" style="border-color: var(--border)">
            <div v-for="c in stats.recent_cases" :key="c.id"
              class="px-5 py-3 flex items-center gap-3 cursor-pointer hover:brightness-110 transition-all"
              @click="router.push(`/cases/${c.id}`)">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate" style="color: var(--text-primary)">{{ c.title }}</p>
                <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ c.case_number }} · {{ fmtDate(c.created_at) }}</p>
              </div>
              <div class="flex gap-1.5 shrink-0">
                <span class="badge"
                  :class="{ 'badge-blue': c.status === 'open', 'badge-green': c.status === 'active', 'badge-slate': ['closed','archived'].includes(c.status) }">
                  {{ c.status }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Scans -->
        <div class="card">
          <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color: var(--border)">
            <h2 class="font-semibold" style="color: var(--text-primary)">Recent Scans</h2>
            <button class="text-xs btn-ghost" @click="showCreateModal = true">+ New →</button>
          </div>
          <div v-if="stats.recent_scans.length === 0" class="p-8 text-center" style="color: var(--text-muted)">
            No scans yet.
          </div>
          <div v-else class="divide-y" style="border-color: var(--border)">
            <div v-for="s in stats.recent_scans" :key="s.id"
              class="px-5 py-3 flex items-center gap-3 cursor-pointer hover:brightness-110 transition-all"
              @click="router.push(`/scan/${s.id}`)">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate" style="color: var(--text-primary)">{{ s.seed_value }}</p>
                <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ s.seed_kind }} · {{ fmtDate(s.created_at) }}</p>
              </div>
              <span class="badge shrink-0" :class="statusBadge[s.status] || 'badge-slate'">{{ s.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>

  <CreateScanModal v-if="showCreateModal" @close="showCreateModal = false" @created="() => { showCreateModal = false; api.getStats().then(r => stats.value = r.data) }" />
</template>
