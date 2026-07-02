<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCasesStore } from '../stores/cases'
import GraphVisualization from '../components/GraphVisualization.vue'
import GraphSidebar from '../components/GraphSidebar.vue'
import GraphNodePanel from '../components/GraphNodePanel.vue'
import CreateScanModal from '../components/CreateScanModal.vue'
import CaseEditModal from '../components/CaseEditModal.vue'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const casesStore = useCasesStore()

const caseId    = computed(() => route.params.id)
const activeTab = ref('scans')
const tabs      = ['scans', 'graph', 'timeline', 'notes', 'reports']

const showScanModal  = ref(false)
const showEditModal  = ref(false)
const newNote        = ref('')
const showReportModal = ref(false)
const reportForm     = ref({ title: '', report_type: 'summary', report_format: 'markdown' })
const selectedNode   = ref(null)
const scanFromNode   = ref(null)
const showNodeScan   = ref(false)
const nodeSuggestedModules = ref([])

onMounted(async () => {
  await loadCase(caseId.value)
})

watch(
  () => route.params.id,
  async (nextCaseId, previousCaseId) => {
    if (nextCaseId && nextCaseId !== previousCaseId) {
      activeTab.value = 'scans'
      selectedNode.value = null
      scanFromNode.value = null
      showNodeScan.value = false
      await loadCase(nextCaseId)
    }
  }
)

async function loadCase(id) {
  await casesStore.fetchCase(id)
  await casesStore.fetchCaseScans(id)
  await casesStore.fetchCaseNotes(id)
  await casesStore.fetchCaseReports(id)
}

function currentCaseId() {
  return caseId.value
}

const currentCase = computed(() => casesStore.currentCase)
const scans       = computed(() => casesStore.caseScans)
const notes       = computed(() => casesStore.caseNotes)
const reports     = computed(() => casesStore.caseReports)
const caseGraph   = computed(() => casesStore.caseGraph)
const nodeParentScanId = computed(() => resolveNodeParentScanId(scanFromNode.value))

// Normalise case graph: the API returns scan_origins on nodes/edges,
// but GraphVisualization expects source/target not scan_origins on edges.
// The data shape already matches — just pass it through.

const timeline = computed(() => {
  const events = []
  if (currentCase.value) {
    events.push({ time: currentCase.value.created_at, type: 'case', label: 'Case created', detail: currentCase.value.title })
  }
  for (const s of scans.value) {
    events.push({ time: s.created_at, type: 'scan', label: 'Scan started', detail: `${s.seed_value} (${s.seed_kind})` })
    if (s.finished_at) {
      const label = s.status === 'partial'
        ? 'Scan partially completed'
        : s.status === 'failed'
          ? 'Scan failed'
          : 'Scan completed'
      events.push({ time: s.finished_at, type: s.status === 'failed' ? 'scan_failed' : 'scan_done', label, detail: s.seed_value })
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

const statusMap  = { open: 'badge-blue', active: 'badge-green', closed: 'badge-slate', archived: 'badge-slate' }
const priorityMap = { critical: 'badge-red', high: 'badge-amber', medium: 'badge-blue', low: 'badge-slate' }

function fmtDate(d) {
  return new Date(d).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function statusIcon(s) {
  return { queued: '⏳', running: '🔄', completed: '✅', partial: '⚠️', failed: '❌', error: '❌' }[s] || '•'
}
function rootScans(all) { return all.filter(s => !s.parent_scan_id) }
function childScans(all, pid) { return all.filter(s => s.parent_scan_id === pid) }

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'graph' && casesStore.caseGraphCaseId !== currentCaseId()) {
    await casesStore.fetchCaseGraph(currentCaseId())
  }
}

async function addNote() {
  if (!newNote.value.trim()) return
  await casesStore.createNote(currentCaseId(), { content: newNote.value })
  newNote.value = ''
}

async function submitReport() {
  await casesStore.createReport(currentCaseId(), reportForm.value)
  showReportModal.value = false
  reportForm.value = { title: '', report_type: 'summary', report_format: 'markdown' }
}

function deleteNote(id)   { casesStore.deleteNote(currentCaseId(), id) }
function deleteReport(id) { casesStore.deleteReport(id) }

async function downloadReport(r) {
  const extMap = { markdown: 'md', text: 'txt', html: 'html', pdf: 'pdf' }
  const ext = extMap[r.report_format] || 'md'
  const filename = `${r.title.replace(/\s+/g, '_')}.${ext}`

  const res = await fetch(api.downloadReportUrl(r.id))
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function previewReport(r) {
  window.open(api.previewReport(r.id), '_blank')
}

function onNodeSelect(node) {
  selectedNode.value = node
}

async function quickStatus(status) {
  await casesStore.updateCase(currentCaseId(), { status })
}

async function quickPriority(priority) {
  await casesStore.updateCase(currentCaseId(), { priority })
}

function unique(values) {
  return [...new Set(values.filter(Boolean))]
}

function resolveOriginScanId(origin, availableScans) {
  if (!origin) return null
  if (typeof origin === 'object') return origin.id || origin.scan_id || null
  if (availableScans.some(s => s.id === origin)) return origin
  return null
}

function resolveNodeParentScanId(node) {
  if (!node) return null

  const availableScans = caseGraph.value?.scans?.length ? caseGraph.value.scans : scans.value
  const origins = Array.isArray(node.scan_origins) ? node.scan_origins : []

  const explicitIds = unique(origins.map(origin => resolveOriginScanId(origin, availableScans)))
  if (explicitIds.length === 1) return explicitIds[0]

  const originLabels = origins.filter(origin => typeof origin === 'string')
  const matchedIds = unique(
    availableScans
      .filter(scan => originLabels.includes(scan.seed_value))
      .map(scan => scan.id)
  )
  if (matchedIds.length === 1) return matchedIds[0]

  const seedMatchIds = unique(
    availableScans
      .filter(scan => scan.seed_value === node.value)
      .map(scan => scan.id)
  )
  return seedMatchIds.length === 1 ? seedMatchIds[0] : null
}

async function openScanFromNode(node) {
  scanFromNode.value = node
  nodeSuggestedModules.value = []
  try {
    const { data } = await api.suggestModules(node.kind)
    nodeSuggestedModules.value = data.map(module => module.module_id)
  } catch {
    nodeSuggestedModules.value = []
  }
  showNodeScan.value = true
}
</script>

<template>
  <!-- Outer: full-height flex column, no scroll — tabs control inner layout -->
  <div class="h-full flex flex-col overflow-hidden">

    <!-- Loading -->
    <div v-if="casesStore.loading && !currentCase" class="flex items-center justify-center h-full">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <template v-else-if="currentCase">

      <!-- ── Case header (always visible) ──────────────────── -->
      <div class="shrink-0 px-6 pt-5 pb-0" style="background-color: var(--bg-primary)">
        <button class="flex items-center gap-1 text-sm mb-3 btn-ghost" @click="router.push('/cases')">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
          Cases
        </button>

        <div class="flex items-start justify-between gap-4 mb-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-mono" style="color: var(--text-muted)">{{ currentCase.case_number }}</span>
              <!-- Quick status dropdown -->
              <select
                :value="currentCase.status"
                class="badge cursor-pointer text-xs border-0 outline-none"
                :class="statusMap[currentCase.status] || 'badge-slate'"
                style="appearance: none; padding-right: 0.5rem; background-color: transparent;"
                @change="quickStatus($event.target.value)"
              >
                <option value="open">open</option>
                <option value="active">active</option>
                <option value="closed">closed</option>
                <option value="archived">archived</option>
              </select>
              <!-- Quick priority dropdown -->
              <select
                :value="currentCase.priority"
                class="badge cursor-pointer text-xs border-0 outline-none"
                :class="priorityMap[currentCase.priority] || 'badge-slate'"
                style="appearance: none; padding-right: 0.5rem; background-color: transparent;"
                @change="quickPriority($event.target.value)"
              >
                <option value="critical">critical</option>
                <option value="high">high</option>
                <option value="medium">medium</option>
                <option value="low">low</option>
              </select>
            </div>
            <h1 class="text-2xl font-bold truncate" style="color: var(--text-primary)">{{ currentCase.title }}</h1>
            <p v-if="currentCase.description" class="text-sm mt-1" style="color: var(--text-secondary)">{{ currentCase.description }}</p>
            <div class="flex flex-wrap gap-2 mt-2">
              <span v-if="currentCase.assigned_to" class="text-xs" style="color: var(--text-muted)">👤 {{ currentCase.assigned_to }}</span>
              <span v-if="currentCase.client" class="text-xs" style="color: var(--text-muted)">🏢 {{ currentCase.client }}</span>
              <span v-for="tag in (currentCase.tags || [])" :key="tag" class="badge badge-slate text-[10px]">{{ tag }}</span>
            </div>
            <div v-if="currentCase.closed_reason && currentCase.status === 'closed'" class="mt-1">
              <span class="text-xs" style="color: var(--text-muted)">Closed: {{ currentCase.closed_reason }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button class="btn-secondary flex items-center gap-2" @click="showEditModal = true">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M11 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-5m-1.414-9.414a2 2 0 1 1 2.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
              Edit
            </button>
            <button class="btn-primary flex items-center gap-2" @click="showScanModal = true">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              Add Scan
            </button>
          </div>
        </div>

        <!-- Tab bar -->
        <div class="flex gap-1 border-b" style="border-color: var(--border)">
          <button v-for="tab in tabs" :key="tab"
            class="tab-btn capitalize"
            :class="{ active: activeTab === tab }"
            @click="switchTab(tab)">
            {{ tab }}
            <span v-if="tab === 'scans'  && scans.length"   class="ml-1.5 badge badge-blue">{{ scans.length }}</span>
            <span v-if="tab === 'notes'  && notes.length"   class="ml-1.5 badge badge-slate">{{ notes.length }}</span>
            <span v-if="tab === 'reports'&& reports.length" class="ml-1.5 badge badge-slate">{{ reports.length }}</span>
          </button>
        </div>
      </div>

      <!-- ── GRAPH TAB — 3-column full-height ──────────────── -->
      <div v-if="activeTab === 'graph'" class="flex-1 flex overflow-hidden">
        <!-- Left sidebar -->
        <GraphSidebar
          :graph-data="caseGraph"
          :seed-value="currentCase.title"
          seed-kind="case"
          @node:select="onNodeSelect"
        />

        <!-- Center canvas -->
        <div class="flex-1 overflow-hidden relative">
          <!-- Loading overlay -->
          <div v-if="casesStore.loading" class="absolute inset-0 flex items-center justify-center z-10" style="background-color: var(--bg-primary)">
            <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
          </div>
          <!-- Empty state -->
          <div v-else-if="!caseGraph?.nodes?.length" class="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <svg class="h-12 w-12 opacity-20" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>
            </svg>
            <p class="text-sm" style="color: var(--text-muted)">No graph data yet. Add scans to this case first.</p>
            <button class="btn-primary" @click="showScanModal = true">Add Scan</button>
          </div>
          <GraphVisualization
            v-else
            :graph-data="caseGraph"
            @node:select="onNodeSelect"
          />
        </div>

        <!-- Right node panel -->
        <GraphNodePanel
          :node="selectedNode"
          :graph-data="caseGraph"
          @close="selectedNode = null"
          @scan-from-node="openScanFromNode"
        />
      </div>

      <!-- ── ALL OTHER TABS — scrollable ────────────────────── -->
      <div v-else class="flex-1 overflow-y-auto p-6">

        <!-- Scans tab -->
        <div v-if="activeTab === 'scans'">
          <div v-if="scans.length === 0" class="flex flex-col items-center justify-center h-36 gap-3">
            <p style="color: var(--text-muted)">No scans yet for this case.</p>
            <button class="btn-primary" @click="showScanModal = true">Add First Scan</button>
          </div>
          <div v-else class="space-y-2">
            <template v-for="s in rootScans(scans)" :key="s.id">
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
              <div v-for="child in childScans(scans, s.id)" :key="child.id"
                class="card p-3 ml-6 flex items-center gap-3 cursor-pointer border-l-2 border-blue-500/30 hover:border-blue-500/60 transition-all"
                @click="router.push(`/scan/${child.id}`)">
                <span class="text-base">{{ statusIcon(child.status) }}</span>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm" style="color: var(--text-primary)">{{ child.seed_value }}</span>
                    <span class="badge badge-purple text-[10px]">child · {{ child.seed_kind }}</span>
                  </div>
                  <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ child.modules.join(', ') }}</p>
                </div>
                <span class="text-xs shrink-0" style="color: var(--text-muted)">{{ fmtDate(child.created_at) }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- Timeline tab -->
        <div v-if="activeTab === 'timeline'" class="space-y-3">
          <div v-if="timeline.length === 0" class="flex items-center justify-center h-24">
            <p style="color: var(--text-muted)">No activity yet.</p>
          </div>
          <div v-for="(ev, i) in timeline" :key="i" class="flex gap-4 items-start">
            <div class="flex flex-col items-center">
              <div class="h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                :class="{
                  'bg-blue-500/20 text-blue-300':    ev.type === 'case',
                  'bg-emerald-500/20 text-emerald-300': ev.type === 'scan_done',
                  'bg-red-500/20 text-red-300':      ev.type === 'scan_failed',
                  'bg-amber-500/20 text-amber-300':  ev.type === 'scan',
                  'bg-purple-500/20 text-purple-300':ev.type === 'report',
                  'bg-slate-500/20 text-slate-300':  ev.type === 'note',
                }">
                {{ { case: '📁', scan: '🔍', scan_done: '✅', scan_failed: '❌', report: '📄', note: '📝' }[ev.type] || '•' }}
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

        <!-- Notes tab -->
        <div v-if="activeTab === 'notes'" class="space-y-4">
          <div class="card p-4">
            <textarea v-model="newNote" class="input h-24 resize-none mb-3" placeholder="Add an investigation note…" />
            <button class="btn-primary" :disabled="!newNote.trim()" @click="addNote">Add Note</button>
          </div>
          <div v-if="notes.length === 0" class="text-center py-6" style="color: var(--text-muted)">No notes yet.</div>
          <div v-for="n in notes" :key="n.id" class="card p-4">
            <div class="flex justify-between items-start gap-2 mb-2">
              <span class="text-xs" style="color: var(--text-muted)">{{ fmtDate(n.created_at) }}{{ n.author ? ' · ' + n.author : '' }}</span>
              <button class="text-xs btn-ghost text-red-400" @click="deleteNote(n.id)">Delete</button>
            </div>
            <p class="text-sm whitespace-pre-wrap" style="color: var(--text-primary)">{{ n.content }}</p>
          </div>
        </div>

        <!-- Reports tab -->
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
                <button v-if="['html','pdf'].includes(r.report_format)" class="btn-ghost text-xs" @click="previewReport(r)">Preview</button>
                <button class="btn-ghost text-xs" @click="downloadReport(r)">Download</button>
                <button class="btn-ghost text-xs text-red-400" @click="deleteReport(r.id)">Delete</button>
              </div>
            </div>
            <div class="flex gap-2 mb-2">
              <span class="badge badge-blue">{{ r.report_type }}</span>
              <span class="badge" :class="r.report_format === 'pdf' ? 'badge-red' : r.report_format === 'html' ? 'badge-amber' : 'badge-slate'">
                {{ r.report_format.toUpperCase() }}
              </span>
            </div>
            <p class="text-xs" style="color: var(--text-muted)">Generated {{ fmtDate(r.generated_at) }}</p>
            <pre v-if="r.content && !['html','pdf'].includes(r.report_format)"
              class="mt-3 text-xs p-3 rounded overflow-auto max-h-40 whitespace-pre-wrap"
              style="background-color: var(--bg-primary); color: var(--text-secondary)">{{ r.content }}</pre>
          </div>
        </div>

      </div>
      <!-- end scrollable tabs -->

    </template>
  </div>

  <!-- Edit case modal -->
  <CaseEditModal
    v-if="showEditModal && currentCase"
    :case-data="currentCase"
    @close="showEditModal = false"
    @saved="casesStore.fetchCase(caseId)"
  />

  <!-- Add scan modal -->
  <CreateScanModal
    v-if="showScanModal"
    :default-case-id="caseId"
    @close="showScanModal = false"
    @created="() => { showScanModal = false; casesStore.fetchCaseScans(caseId); casesStore.fetchCaseGraph(caseId) }"
  />

  <!-- Scan from graph node -->
  <CreateScanModal
    v-if="showNodeScan && scanFromNode"
    :default-case-id="caseId"
    :default-target="scanFromNode.value"
    :default-kind="scanFromNode.kind"
    :parent-scan-id="nodeParentScanId"
    :suggested-modules="nodeSuggestedModules"
    @close="showNodeScan = false; scanFromNode = null; nodeSuggestedModules = []"
    @created="() => { showNodeScan = false; scanFromNode = null; nodeSuggestedModules = []; casesStore.fetchCaseGraph(caseId) }"
  />

  <!-- Report modal -->
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
                <option value="html">HTML</option>
                <option value="pdf">PDF</option>
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
