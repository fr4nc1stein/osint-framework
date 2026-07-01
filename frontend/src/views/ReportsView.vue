<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'

const reports = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.getAllReports()
    reports.value = data
  } finally {
    loading.value = false
  }
})

function fmtDate(d) {
  return new Date(d).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function download(r) {
  const blob = new Blob([r.content || ''], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${r.title.replace(/\s+/g, '_')}.md`
  a.click()
  URL.revokeObjectURL(url)
}

async function del(id) {
  await api.deleteReport(id)
  reports.value = reports.value.filter(r => r.id !== id)
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="page-header">
      <div>
        <h1 class="page-title">Reports</h1>
        <p class="text-sm mt-1" style="color: var(--text-secondary)">All generated investigation reports</p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <div v-else-if="reports.length === 0" class="flex flex-col items-center justify-center h-48 gap-3">
      <svg class="h-12 w-12" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
      </svg>
      <p style="color: var(--text-secondary)">No reports generated yet. Open a case and generate a report.</p>
    </div>

    <div v-else class="space-y-3">
      <div v-for="r in reports" :key="r.id" class="card p-4">
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0">
            <h3 class="font-medium truncate" style="color: var(--text-primary)">{{ r.title }}</h3>
            <p class="text-xs mt-1" style="color: var(--text-muted)">{{ fmtDate(r.generated_at) }} · by {{ r.generated_by }}</p>
            <div class="flex gap-2 mt-2">
              <span class="badge badge-blue">{{ r.report_type }}</span>
              <span class="badge badge-slate">{{ r.report_format }}</span>
            </div>
          </div>
          <div class="flex gap-2 shrink-0">
            <button class="btn-secondary text-sm px-3 py-1.5" @click="download(r)">Download</button>
            <button class="btn-ghost text-sm text-red-400" @click="del(r.id)">Delete</button>
          </div>
        </div>
        <pre v-if="r.content" class="mt-3 text-xs p-3 rounded overflow-auto max-h-32 whitespace-pre-wrap" style="background-color: var(--bg-primary); color: var(--text-secondary)">{{ r.content }}</pre>
      </div>
    </div>
  </div>
</template>
