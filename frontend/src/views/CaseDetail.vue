<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCasesStore } from '../stores/cases'
import { api } from '../api/client'
import CreateScanModal from '../components/CreateScanModal.vue'

const route = useRoute()
const router = useRouter()
const casesStore = useCasesStore()

const caseId = route.params.id
const activeTab = ref('scans')
const tabs = ['scans', 'graph', 'timeline', 'notes', 'reports']

const showScanModal = ref(false)
const newNote = ref('')
const showReportModal = ref(false)
const reportForm = ref({ title: '', report_type: 'summary', report_format: 'markdown' })
const graphContainer = ref(null)
let cy = null

onMounted(async () => {
  await casesStore.fetchCase(caseId)
  await casesStore.fetchCaseScans(caseId)
  await casesStore.fetchCaseNotes(caseId)
  await casesStore.fetchCaseReports(caseId)
})

const currentCase = computed(() => casesStore.currentCase)
const scans = computed(() => casesStore.caseScans)
const notes = computed(() => casesStore.caseNotes)
const reports = computed(() => casesStore.caseReports)

// Build timeline from scans + reports + notes
const timeline = computed(() => {
  const events = []
  if (currentCase.value) {
    events.push({ time: currentCase.value.created_at, type: 'case', label: 'Case created', detail: currentCase.value.title })
  }
  for (const s of scans.value) {
    events.push({ time: s.created_at, type: 'scan', label: 'Scan started', detail: `${s.seed_value} (${s.seed_kind})` })
    if (s.finished_at) {
      events.push({ time: s.finished_at, type: 'scan_done', label: 'Scan completed', detail: s.seed_value })
    }
  }
  for (const r of reports.value) {
    events.push({ time: r.generated_at, type: 'report', label: 'Report generated', detail: r.title })
  }
  for (const n of notes.value) {
    events.push({ time: n.created_at, type: 'note', label: 'Note added', detail: n.content.slice(0, 60) + (n.content.length > 60 ? '…' : '') })
  }
  return events.sort((a, b) => new Date(b.time) - new Date(a.time))
})

const statusMap = { open: 'badge-blue', active: 'badge-green', closed: 'badge-slate', archived: 'badge-slate' }
const priorityMap = { critical: 'badge-red', high: 'badge-amber', medium: 'badge-blue', low: 'badge-slate' }

function fmtDate(d) {
  return new Date(d).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function statusIcon(s) {
  return { queued: '⏳', running: '🔄', completed: '✅', error: '❌' }[s] || '•'
}

async function loadGraph() {
  const data = await casesStore.fetchCaseGraph(caseId)
  if (!data?.nodes?.length) return

  const cytoscape = (await import('cytoscape')).default

  const SCAN_COLORS = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ec4899','#06b6d4']
  const scanColorMap = {}
  data.scans.forEach((s, i) => { scanColorMap[s.seed_value] = SCAN_COLORS[i % SCAN_COLORS.length] })

  const elements = [
    ...data.nodes.map(n => ({
      data: { id: n.id, label: n.value, kind: n.kind, scan_origins: n.scan_origins },
    })),
    ...data.edges.map(e => ({
      data: { id: e.id, source: e.source, target: e.target, label: e.relationship },
    })),
  ]

  if (cy) { cy.destroy(); cy = null }
  cy = cytoscape({
    container: graphContainer.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': (ele) => {
            const origins = ele.data('scan_origins') || []
            return scanColorMap[origins[0]] || '#64748b'
          },
          label: 'data(label)',
          'font-size': 10,
          color: '#f1f5f9',
          'text-outline-color': '#0f172a',
          'text-outline-width': 2,
          'text-valign': 'bottom',
          'text-halign': 'center',
          width: 32,
          height: 32,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#475569',
          'target-arrow-color': '#475569',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          label: 'data(label)',
          'font-size': 8,
          color: '#94a3b8',
        },
      },
    ],
    layout: { name: 'cose', animate: false, randomize: false },
  })
}

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'graph') {
    await new Promise(r => setTimeout(r, 50))
    await loadGraph()
  }
}

async function addNote() {
  if (!newNote.value.trim()) return
  await casesStore.createNote(caseId, { content: newNote.value })
  newNote.value = ''
}

async function submitReport() {
  await casesStore.createReport(caseId, reportForm.value)
  showReportModal.value = false
  reportForm.value = { title: '', report_type: 'summary', report_format: 'markdown' }
}

async function deleteNote(noteId) {
  await casesStore.deleteNote(caseId, noteId)
}

async function deleteReport(reportId) {
  await casesStore.deleteReport(reportId)
}

function downloadReport(report) {
  const blob = new Blob([report.content || ''], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${report.title.replace(/\s+/g, '_')}.md`
  a.click()
  URL.revokeObjectURL(url)
}

// Scan hierarchy tree helpers
function rootScans(all) { return all.filter(s => !s.parent_scan_id) }
function childScans(all, parentId) { return all.filter(s => s.parent_scan_id === parentId) }
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <!-- Loading -->
    <div v-if="casesStore.loading && !currentCase" class="flex items-center justify-center h-48">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <template v-else-if="currentCase">
      <!-- Case Header -->
      <div class="mb-6">
        <button class="flex items-center gap-1 text-sm mb-3 btn-ghost" @click="router.push('/cases')">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
          Cases
        </button>
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-mono" style="color: var(--text-muted)">{{ currentCase.case_number }}</span>
              <span class="badge" :class="statusMap[currentCase.status] || 'badge-slate'">{{ currentCase.status }}</span>
              <span class="badge" :class="priorityMap[currentCase.priority] || 'badge-slate'">{{ currentCase.priority }}</span>
            </div>
            <h1 class="page-title">{{ currentCase.title }}</h1>
            <p v-if="currentCase.description" class="text-sm mt-1" style="color: var(--text-secondary)">{{ currentCase.description }}</p>
          </div>
          <button class="btn-primary shrink-0 flex items-center gap-2" @click="showScanModal = true">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            Add Scan
          </button>
        </div>

        <div class="flex flex-wrap gap-2 mt-3">
          <span v-if="currentCase.assigned_to" class="text-xs" style="color: var(--text-muted)">
            👤 {{ currentCase.assigned_to }}
          </span>
          <span v-for="tag in (currentCase.tags || [])" :key="tag" class="badge badge-slate text-[10px]">{{ tag }}</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tab-bar">
        <button v-for="tab in tabs" :key="tab"
          class="tab-btn capitalize"
          :class="{ active: activeTab === tab }"
          @click="switchTab(tab)"
        >
          {{ tab }}
          <span v-if="tab === 'scans' && scans.length" class="ml-1.5 badge badge-blue">{{ scans.length }}</span>
          <span v-if="tab === 'notes' && notes.length" class="ml-1.5 badge badge-slate">{{ notes.length }}</span>
          <span v-if="tab === 'reports' && reports.length" class="ml-1.5 badge badge-slate">{{ reports.length }}</span>
        </button>
      </div>

      <!-- ── Scans tab ─────────────────────────────────────── -->
      <div v-if="activeTab === 'scans'">
        <div v-if="scans.length === 0" class="flex flex-col items-center justify-center h-36 gap-3">
          <p style="color: var(--text-muted)">No scans yet for this case.</p>
          <button class="btn-primary" @click="showScanModal = true">Add First Scan</button>
        </div>

        <!-- Scan tree -->
        <div v-else class="space-y-2">
          <template v-for="s in rootScans(scans)" :key="s.id">
            <!-- Parent scan -->
            <div class="card p-3 flex items-center gap-3 cursor-pointer hover:border-blue-500/30 transition-all"
              @click="router.push(`/scan/${s.id}`)">
              <span class="text-lg">{{ statusIcon(s.status) }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-sm" style="color: var(--text-primary)">{{ s.seed_value }}</span>
                  <span class="badge badge-blue text-[10px]">{{ s.seed_kind }}</span>
                </div>
                <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ s.modules.join(', ') }}</p>
              </div>
              <span class="text-xs shrink-0" style="color: var(--text-muted)">{{ fmtDate(s.created_at) }}</span>
            </div>

            <!-- Child scans indented -->
            <div v-for="child in childScans(scans, s.id)" :key="child.id"
              class="card p-3 ml-6 flex items-center gap-3 cursor-pointer border-l-2 border-blue-500/30 hover:border-blue-500/60 transition-all"
              @click="router.push(`/scan/${child.id}`)">
              <span class="text-base">{{ statusIcon(child.status) }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-sm" style="color: var(--text-primary)">{{ child.seed_value }}</span>
                  <span class="badge badge-purple text-[10px]">child • {{ child.seed_kind }}</span>
                </div>
                <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ child.modules.join(', ') }}</p>
              </div>
              <span class="text-xs shrink-0" style="color: var(--text-muted)">{{ fmtDate(child.created_at) }}</span>
            </div>
          </template>
        </div>
      </div>

      <!-- ── Graph tab ──────────────────────────────────────── -->
      <div v-if="activeTab === 'graph'" class="h-[calc(100vh-280px)] min-h-[400px]">
        <div v-if="!casesStore.caseGraph && !casesStore.loading" class="flex items-center justify-center h-24">
          <p style="color: var(--text-muted)">Loading graph…</p>
        </div>
        <div v-else-if="casesStore.caseGraph?.nodes?.length === 0" class="flex items-center justify-center h-24">
          <p style="color: var(--text-muted)">No graph data yet. Run some scans first.</p>
        </div>
        <div ref="graphContainer" class="w-full h-full rounded-lg border" style="background-color: var(--bg-secondary); border-color: var(--border)"></div>
      </div>

      <!-- ── Timeline tab ───────────────────────────────────── -->
      <div v-if="activeTab === 'timeline'" class="space-y-3">
        <div v-if="timeline.length === 0" class="flex items-center justify-center h-24">
          <p style="color: var(--text-muted)">No activity yet.</p>
        </div>
        <div v-for="(ev, i) in timeline" :key="i" class="flex gap-4 items-start">
          <div class="flex flex-col items-center">
            <div class="h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
              :class="{
                'bg-blue-500/20 text-blue-300': ev.type === 'case',
                'bg-emerald-500/20 text-emerald-300': ev.type === 'scan_done',
                'bg-amber-500/20 text-amber-300': ev.type === 'scan',
                'bg-purple-500/20 text-purple-300': ev.type === 'report',
                'bg-slate-500/20 text-slate-300': ev.type === 'note',
              }">
              {{ { case: '📁', scan: '🔍', scan_done: '✅', report: '📄', note: '📝' }[ev.type] || '•' }}
            </div>
            <div v-if="i < timeline.length - 1" class="w-0.5 flex-1 my-1" style="background-color: var(--border)"></div>
          </div>
          <div class="pb-4">
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ ev.label }}</p>
            <p class="text-sm" style="color: var(--text-secondary)">{{ ev.detail }}</p>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ fmtDate(ev.time) }}</p>
          </div>
        </div>
      </div>

      <!-- ── Notes tab ──────────────────────────────────────── -->
      <div v-if="activeTab === 'notes'" class="space-y-4">
        <!-- Add note -->
        <div class="card p-4">
          <textarea v-model="newNote" class="input h-24 resize-none mb-3" placeholder="Add an investigation note…" />
          <button class="btn-primary" :disabled="!newNote.trim()" @click="addNote">Add Note</button>
        </div>
        <!-- Notes list -->
        <div v-if="notes.length === 0" class="text-center py-6" style="color: var(--text-muted)">No notes yet.</div>
        <div v-for="n in notes" :key="n.id" class="card p-4">
          <div class="flex justify-between items-start gap-2 mb-2">
            <span class="text-xs" style="color: var(--text-muted)">{{ fmtDate(n.created_at) }}{{ n.author ? ' · ' + n.author : '' }}</span>
            <button class="text-xs btn-ghost text-red-400 hover:text-red-300" @click="deleteNote(n.id)">Delete</button>
          </div>
          <p class="text-sm whitespace-pre-wrap" style="color: var(--text-primary)">{{ n.content }}</p>
        </div>
      </div>

      <!-- ── Reports tab ────────────────────────────────────── -->
      <div v-if="activeTab === 'reports'">
        <div class="flex justify-end mb-4">
          <button class="btn-primary flex items-center gap-2" @click="showReportModal = true">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            Generate Report
          </button>
        </div>
        <div v-if="reports.length === 0" class="text-center py-12" style="color: var(--text-muted)">No reports yet.</div>
        <div v-for="r in reports" :key="r.id" class="card p-4 mb-3">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-medium" style="color: var(--text-primary)">{{ r.title }}</h3>
            <div class="flex gap-2">
              <button class="btn-ghost text-xs" @click="downloadReport(r)">Download</button>
              <button class="btn-ghost text-xs text-red-400" @click="deleteReport(r.id)">Delete</button>
            </div>
          </div>
          <div class="flex gap-2 mb-2">
            <span class="badge badge-blue">{{ r.report_type }}</span>
            <span class="badge badge-slate">{{ r.report_format }}</span>
          </div>
          <p class="text-xs" style="color: var(--text-muted)">Generated {{ fmtDate(r.generated_at) }}</p>
          <pre v-if="r.content" class="mt-3 text-xs p-3 rounded overflow-auto max-h-40 whitespace-pre-wrap" style="background-color: var(--bg-primary); color: var(--text-secondary)">{{ r.content }}</pre>
        </div>
      </div>
    </template>
  </div>

  <!-- Scan creation modal -->
  <CreateScanModal
    v-if="showScanModal"
    :default-case-id="caseId"
    @close="showScanModal = false"
    @created="(id) => { showScanModal = false; casesStore.fetchCaseScans(caseId) }"
  />

  <!-- Report generation modal -->
  <Teleport to="body">
    <div v-if="showReportModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showReportModal = false">
      <div class="card p-6 w-full max-w-md mx-4">
        <h2 class="text-lg font-semibold mb-4" style="color: var(--text-primary)">Generate Report</h2>
        <form @submit.prevent="submitReport" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Title *</label>
            <input v-model="reportForm.title" class="input" placeholder="Report title" required />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Type</label>
              <select v-model="reportForm.report_type" class="input">
                <option value="summary">Executive Summary</option>
                <option value="technical">Technical Details</option>
                <option value="timeline">Timeline</option>
                <option value="full">Full Report</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Format</label>
              <select v-model="reportForm.report_format" class="input">
                <option value="markdown">Markdown</option>
                <option value="text">Plain Text</option>
              </select>
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn-secondary" @click="showReportModal = false">Cancel</button>
            <button type="submit" class="btn-primary">Generate</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
