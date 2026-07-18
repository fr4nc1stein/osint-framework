<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import CreateTemplateModal from '../components/CreateTemplateModal.vue'

const router = useRouter()
const templates = ref([])
const loading = ref(false)
const showCreateModal = ref(false)

async function fetchTemplates() {
  loading.value = true
  try {
    const { data } = await api.getTemplates()
    templates.value = data
  } finally {
    loading.value = false
  }
}

function useTemplate(template) {
  router.push({ path: '/', query: { template: template.id } })
}

async function deleteTemplate(id) {
  if (!confirm('Delete this template?')) return
  await api.deleteTemplate(id)
  templates.value = templates.value.filter(t => t.id !== id)
}

onMounted(fetchTemplates)
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Scan Templates</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">Reusable scan configurations</p>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="showCreateModal = true">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        New Template
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="templates.length === 0" class="flex flex-col items-center justify-center h-48 gap-3">
      <svg class="h-12 w-12" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path d="M8 2h8l4 4v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/>
        <path d="M16 2v5h5"/><path d="M10 13h6M10 17h4"/>
      </svg>
      <p style="color: var(--text-secondary)">No templates yet. Create one to reuse scan configs.</p>
      <button class="btn-primary" @click="showCreateModal = true">New Template</button>
    </div>

    <!-- Templates grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="t in templates" :key="t.id" class="card p-5 flex flex-col gap-4">
        <!-- Header -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold truncate" style="color: var(--text-primary)">{{ t.name }}</h3>
            <p v-if="t.description" class="text-sm mt-0.5 line-clamp-2" style="color: var(--text-secondary)">{{ t.description }}</p>
          </div>
          <span class="badge badge-blue shrink-0">{{ t.category }}</span>
        </div>

        <!-- Modules -->
        <div>
          <p class="text-xs mb-2" style="color: var(--text-muted)">Modules ({{ t.modules.length }})</p>
          <div class="flex flex-wrap gap-1">
            <span v-for="m in t.modules.slice(0, 5)" :key="m"
              class="badge badge-slate text-[10px]">{{ m }}</span>
            <span v-if="t.modules.length > 5" class="text-xs" style="color: var(--text-muted)">+{{ t.modules.length - 5 }} more</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-2 mt-auto">
          <button class="btn-primary flex-1 text-sm py-2" @click="useTemplate(t)">Use Template</button>
          <button class="btn-ghost text-sm text-red-400 px-3" @click="deleteTemplate(t.id)">Delete</button>
        </div>
      </div>
    </div>
  </div>

  <CreateTemplateModal v-if="showCreateModal" @close="showCreateModal = false" @created="() => { showCreateModal = false; fetchTemplates() }" />
</template>
