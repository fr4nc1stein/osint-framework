<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScansStore } from '../stores/scans'
import CreateScanModal from '../components/CreateScanModal.vue'

const router = useRouter()
const scansStore = useScansStore()

const showCreateModal = ref(false)
const filterStatus = ref('all')

onMounted(() => scansStore.fetchScans())

const filtered = computed(() => {
  const all = scansStore.scans
  if (filterStatus.value === 'all') return all
  return all.filter(s => s.status === filterStatus.value)
})

const statusBadge = {
  queued:    'badge-slate',
  running:   'badge-blue',
  completed: 'badge-green',
  partial:   'badge-amber',
  failed:    'badge-red',
  error:     'badge-red',
}

const statusIcon = {
  queued: '⏳', running: '🔄', completed: '✅', partial: '⚠️', failed: '❌', error: '❌',
}

function fmtDate(d) {
  const diff = Date.now() - new Date(d).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Scans</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">All OSINT scan jobs</p>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="showCreateModal = true">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        New Scan
      </button>
    </div>

    <!-- Filter bar -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="f in ['all','queued','running','completed','partial','failed','error']" :key="f"
        class="px-3 py-1.5 rounded-md text-sm font-medium transition-all"
        :style="filterStatus === f
          ? 'background-color: var(--accent); color: #fff'
          : 'background-color: var(--bg-secondary); color: var(--text-secondary)'"
        @click="filterStatus = f"
      >
        {{ f.charAt(0).toUpperCase() + f.slice(1) }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="scansStore.loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="filtered.length === 0" class="flex flex-col items-center justify-center h-48 gap-3">
      <svg class="h-12 w-12" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <p style="color: var(--text-secondary)">No scans yet.</p>
      <button class="btn-primary" @click="showCreateModal = true">New Scan</button>
    </div>

    <!-- Scans list -->
    <div v-else class="card divide-y" style="border-color: var(--border)">
      <div
        v-for="s in filtered" :key="s.id"
        class="px-5 py-4 flex items-center gap-4 cursor-pointer transition-all hover:brightness-110"
        @click="router.push(`/scan/${s.id}`)"
      >
        <span class="text-xl shrink-0">{{ statusIcon[s.status] || '•' }}</span>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="font-medium text-sm" style="color: var(--text-primary)">{{ s.seed_value }}</span>
            <span class="badge badge-blue text-[10px]">{{ s.seed_kind }}</span>
            <span v-if="s.case_id" class="badge badge-purple text-[10px]">in case</span>
          </div>
          <p class="text-xs" style="color: var(--text-muted)">
            {{ s.modules.length }} module{{ s.modules.length !== 1 ? 's' : '' }} · {{ fmtDate(s.created_at) }}
          </p>
        </div>

        <div class="flex items-center gap-3 shrink-0">
          <!-- Progress bar (only for running scans) -->
          <div v-if="s.status === 'running' && s.total_modules > 0" class="w-24">
            <div class="flex justify-between text-xs mb-1" style="color: var(--text-muted)">
              <span>{{ s.progress }}/{{ s.total_modules }}</span>
            </div>
            <div class="h-1.5 rounded-full overflow-hidden" style="background-color: var(--bg-tertiary)">
              <div class="h-full rounded-full bg-blue-500 transition-all"
                :style="`width: ${Math.round((s.progress / s.total_modules) * 100)}%`"></div>
            </div>
          </div>
          <span class="badge" :class="statusBadge[s.status] || 'badge-slate'">{{ s.status }}</span>
          <svg class="h-4 w-4" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </div>
      </div>
    </div>
  </div>

  <CreateScanModal v-if="showCreateModal" @close="showCreateModal = false" @created="() => { showCreateModal = false; scansStore.fetchScans() }" />
</template>
