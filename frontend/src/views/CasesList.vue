<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCasesStore } from '../stores/cases'

const router = useRouter()
const casesStore = useCasesStore()

const showCreateModal = ref(false)
const filterStatus = ref('all')

const form = ref({ title: '', description: '', priority: 'medium', status: 'open', assigned_to: '', tags: '' })

onMounted(() => casesStore.fetchCases())

const filtered = computed(() => {
  if (filterStatus.value === 'all') return casesStore.cases
  return casesStore.cases.filter(c => c.status === filterStatus.value)
})

const statusMap = {
  open:     { label: 'Open',     cls: 'badge-blue'   },
  active:   { label: 'Active',   cls: 'badge-green'  },
  closed:   { label: 'Closed',   cls: 'badge-slate'  },
  archived: { label: 'Archived', cls: 'badge-slate'  },
}
const priorityMap = {
  critical: { label: 'Critical', cls: 'badge-red'    },
  high:     { label: 'High',     cls: 'badge-amber'  },
  medium:   { label: 'Medium',   cls: 'badge-blue'   },
  low:      { label: 'Low',      cls: 'badge-slate'  },
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

async function submit() {
  const payload = {
    ...form.value,
    tags: form.value.tags ? form.value.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
  }
  const c = await casesStore.createCase(payload)
  showCreateModal.value = false
  form.value = { title: '', description: '', priority: 'medium', status: 'open', assigned_to: '', tags: '' }
  router.push(`/cases/${c.id}`)
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Cases</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">Manage your investigation cases</p>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="showCreateModal = true">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        New Case
      </button>
    </div>

    <!-- Filter bar -->
    <div class="flex gap-2 mb-6">
      <button v-for="f in ['all','open','active','closed']" :key="f"
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
    <div v-if="casesStore.loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="filtered.length === 0" class="flex flex-col items-center justify-center h-48 gap-3">
      <svg class="h-12 w-12" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      </svg>
      <p style="color: var(--text-secondary)">No cases yet. Create your first investigation.</p>
      <button class="btn-primary" @click="showCreateModal = true">New Case</button>
    </div>

    <!-- Cases grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div
        v-for="c in filtered" :key="c.id"
        class="card p-4 cursor-pointer hover:border-blue-500/40 transition-all duration-150"
        @click="router.push(`/cases/${c.id}`)"
      >
        <div class="flex items-start justify-between gap-2 mb-2">
          <span class="text-xs font-mono" style="color: var(--text-muted)">{{ c.case_number }}</span>
          <div class="flex gap-1.5">
            <span class="badge" :class="statusMap[c.status]?.cls || 'badge-slate'">
              {{ statusMap[c.status]?.label || c.status }}
            </span>
            <span class="badge" :class="priorityMap[c.priority]?.cls || 'badge-slate'">
              {{ priorityMap[c.priority]?.label || c.priority }}
            </span>
          </div>
        </div>

        <h3 class="font-semibold mb-1 line-clamp-1" style="color: var(--text-primary)">{{ c.title }}</h3>
        <p v-if="c.description" class="text-sm mb-3 line-clamp-2" style="color: var(--text-secondary)">{{ c.description }}</p>

        <div class="flex items-center justify-between text-xs mt-3 pt-3 border-t" style="border-color: var(--border); color: var(--text-muted)">
          <span v-if="c.assigned_to">{{ c.assigned_to }}</span>
          <span v-else>Unassigned</span>
          <span>{{ fmtDate(c.created_at) }}</span>
        </div>

        <div v-if="c.tags?.length" class="flex flex-wrap gap-1 mt-2">
          <span v-for="tag in c.tags.slice(0,4)" :key="tag" class="badge badge-slate text-[10px]">{{ tag }}</span>
        </div>
      </div>
    </div>

    <!-- Create Case Modal -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showCreateModal = false">
        <div class="card p-6 w-full max-w-md mx-4">
          <h2 class="text-lg font-semibold mb-4" style="color: var(--text-primary)">Create New Case</h2>

          <form @submit.prevent="submit" class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Title *</label>
              <input v-model="form.title" class="input" placeholder="Investigation title" required />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Description</label>
              <textarea v-model="form.description" class="input h-20 resize-none" placeholder="What are you investigating?" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Priority</label>
                <select v-model="form.priority" class="input">
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Status</label>
                <select v-model="form.status" class="input">
                  <option value="open">Open</option>
                  <option value="active">Active</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Assigned To</label>
              <input v-model="form.assigned_to" class="input" placeholder="Investigator name" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Tags (comma separated)</label>
              <input v-model="form.tags" class="input" placeholder="malware, phishing, apt" />
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" class="btn-secondary" @click="showCreateModal = false">Cancel</button>
              <button type="submit" class="btn-primary" :disabled="!form.title">Create Case</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>
