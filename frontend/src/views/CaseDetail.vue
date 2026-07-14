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
const tabs      = ['scans', 'graph', 'timeline', 'evidence', 'notes', 'reports']

const showScanModal  = ref(false)
const showEditModal  = ref(false)
const newNote        = ref('')
const showReportModal = ref(false)
const reportForm     = ref({ title: '', report_type: 'summary', report_format: 'markdown' })
const selectedNode   = ref(null)
const scanFromNode   = ref(null)
const showNodeScan   = ref(false)
const nodeSuggestedModules = ref([])
const showEntityModal = ref(false)
const showRelationshipModal = ref(false)
const showEvidenceModal = ref(false)
const entityRelationNode = ref(null)
const evidenceTarget = ref(null)
const entityForm = ref(defaultEntityForm())
const relationshipForm = ref(defaultRelationshipForm())
const evidenceForm = ref(defaultEvidenceForm())
const evidenceFile = ref(null)
const evidenceError = ref('')
const selectedNodeEvidence = ref([])
const selectedNodeEvidenceLoading = ref(false)

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
  await casesStore.fetchCaseEvidence(id)
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
const evidence    = computed(() => casesStore.caseEvidence)
const caseGraph   = computed(() => casesStore.caseGraph)
const nodeParentScanId = computed(() => resolveNodeParentScanId(scanFromNode.value))
const graphNodes = computed(() => caseGraph.value?.nodes ?? [])

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
  for (const item of evidence.value) {
    events.push({ time: item.created_at, type: 'evidence', label: 'Evidence added', detail: item.title })
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
  if (tab === 'evidence' && casesStore.caseEvidenceCaseId !== currentCaseId()) {
    await casesStore.fetchCaseEvidence(currentCaseId())
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
  loadSelectedNodeEvidence(node)
}

function closeSelectedNode() {
  selectedNode.value = null
  selectedNodeEvidence.value = []
  selectedNodeEvidenceLoading.value = false
}

function defaultEntityForm() {
  return {
    type: 'person',
    label: '',
    value: '',
    description: '',
    confidence: '0.6',
    verification_status: 'lead',
    relationship_type: 'associated_with',
    relationship_label: '',
  }
}

function defaultRelationshipForm() {
  return {
    from_node_id: '',
    to_node_id: '',
    relationship_type: 'associated_with',
    label: '',
    description: '',
    confidence: '0.6',
    verification_status: 'lead',
  }
}

function defaultEvidenceForm() {
  return {
    mode: 'file',
    title: '',
    description: '',
    evidence_type: 'document',
    source_url: '',
    collected_by: '',
    relationship_note: '',
  }
}

function graphNodeType(node) {
  return node?.graph_node_type ?? (node?.source_type === 'scan' ? 'indicator' : 'entity')
}

function graphNodeLabel(node) {
  if (!node) return ''
  if (node.__evidence_label) return node.__evidence_label
  return `${node.kind || graphNodeType(node)} · ${node.label || node.value}`
}

function evidenceTargetType(target) {
  return target?.__evidence_target_type || graphNodeType(target)
}

function evidenceTargetId(target) {
  return target?.__evidence_target_id || target?.id
}

async function loadSelectedNodeEvidence(node = selectedNode.value) {
  selectedNodeEvidence.value = []
  if (!node) return

  selectedNodeEvidenceLoading.value = true
  const targetType = graphNodeType(node)
  const targetId = node.id
  try {
    const items = await casesStore.fetchCaseEvidence(currentCaseId(), {
      target_type: targetType,
      target_id: targetId,
    })
    if (selectedNode.value?.id === targetId) {
      selectedNodeEvidence.value = items
    }
  } catch {
    if (selectedNode.value?.id === targetId) {
      selectedNodeEvidence.value = []
    }
  } finally {
    if (selectedNode.value?.id === targetId) {
      selectedNodeEvidenceLoading.value = false
    }
  }
}

function isSelectedNodeTarget(target) {
  if (!selectedNode.value || !target) return false
  return evidenceTargetType(target) === graphNodeType(selectedNode.value)
    && evidenceTargetId(target) === selectedNode.value.id
}

function nodeById(id) {
  return graphNodes.value.find(node => node.id === id)
}

function openEntityModal(connectedNode = null) {
  entityRelationNode.value = connectedNode
  entityForm.value = defaultEntityForm()
  showEntityModal.value = true
}

function openRelationshipModal(sourceNode = null) {
  relationshipForm.value = defaultRelationshipForm()
  if (sourceNode) relationshipForm.value.from_node_id = sourceNode.id
  showRelationshipModal.value = true
}

async function submitEntity() {
  const confidence = entityForm.value.confidence === '' ? null : Number(entityForm.value.confidence)
  const payload = {
    type: entityForm.value.type,
    label: entityForm.value.label,
    value: entityForm.value.value,
    description: entityForm.value.description || null,
    confidence,
    verification_status: entityForm.value.verification_status,
    properties: {},
  }

  if (entityRelationNode.value) {
    payload.connected_to_node_type = graphNodeType(entityRelationNode.value)
    payload.connected_to_node_id = entityRelationNode.value.id
    payload.relationship_type = entityForm.value.relationship_type || 'associated_with'
    payload.relationship_label = entityForm.value.relationship_label || null
  }

  await casesStore.createCaseEntity(currentCaseId(), payload)
  showEntityModal.value = false
  entityRelationNode.value = null
  selectedNode.value = null
}

async function submitRelationship() {
  if (!relationshipForm.value.from_node_id || !relationshipForm.value.to_node_id) return
  if (relationshipForm.value.from_node_id === relationshipForm.value.to_node_id) return

  const fromNode = nodeById(relationshipForm.value.from_node_id)
  const toNode = nodeById(relationshipForm.value.to_node_id)
  if (!fromNode || !toNode) return

  const confidence = relationshipForm.value.confidence === '' ? null : Number(relationshipForm.value.confidence)
  await casesStore.createCaseRelationship(currentCaseId(), {
    from_node_type: graphNodeType(fromNode),
    from_node_id: fromNode.id,
    to_node_type: graphNodeType(toNode),
    to_node_id: toNode.id,
    relationship_type: relationshipForm.value.relationship_type,
    label: relationshipForm.value.label || null,
    description: relationshipForm.value.description || null,
    confidence,
    verification_status: relationshipForm.value.verification_status,
    properties: {},
  })

  showRelationshipModal.value = false
  selectedNode.value = null
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

function openEvidenceModal(target = null) {
  evidenceTarget.value = target
  evidenceForm.value = defaultEvidenceForm()
  evidenceFile.value = null
  evidenceError.value = ''
  if (target) {
    evidenceForm.value.title = `Evidence for ${target.label || target.value}`
  }
  showEvidenceModal.value = true
}

function onEvidenceFileChange(event) {
  evidenceFile.value = event.target.files?.[0] || null
}

function inferEvidenceType(file) {
  if (!file) return evidenceForm.value.evidence_type
  if (file.type?.startsWith('image/')) return 'image'
  if (file.type === 'application/pdf') return 'pdf'
  if (file.type?.startsWith('text/')) return 'text'
  return evidenceForm.value.evidence_type || 'document'
}

async function submitEvidence() {
  evidenceError.value = ''
  const target = evidenceTarget.value
  try {
    if (evidenceForm.value.mode === 'file') {
      if (!evidenceFile.value) {
        evidenceError.value = 'Select a file to upload.'
        return
      }
      const formData = new FormData()
      formData.append('title', evidenceForm.value.title)
      formData.append('evidence_type', inferEvidenceType(evidenceFile.value))
      formData.append('source_type', 'manual')
      if (evidenceForm.value.description) formData.append('description', evidenceForm.value.description)
      if (evidenceForm.value.source_url) formData.append('source_url', evidenceForm.value.source_url)
      if (evidenceForm.value.collected_by) formData.append('collected_by', evidenceForm.value.collected_by)
      if (target) {
        formData.append('target_type', evidenceTargetType(target))
        formData.append('target_id', evidenceTargetId(target))
        if (evidenceForm.value.relationship_note) formData.append('relationship_note', evidenceForm.value.relationship_note)
      }
      formData.append('file', evidenceFile.value)
      await casesStore.uploadCaseEvidence(currentCaseId(), formData)
    } else {
      const payload = {
        title: evidenceForm.value.title,
        description: evidenceForm.value.description || null,
        evidence_type: evidenceForm.value.mode === 'url' ? 'url' : 'note',
        source_type: 'manual',
        source_url: evidenceForm.value.mode === 'url' ? evidenceForm.value.source_url : null,
        collected_by: evidenceForm.value.collected_by || null,
      }
      if (target) {
        payload.link = {
          target_type: evidenceTargetType(target),
          target_id: evidenceTargetId(target),
          relationship_note: evidenceForm.value.relationship_note || null,
        }
      }
      await casesStore.createCaseEvidence(currentCaseId(), payload)
    }
    showEvidenceModal.value = false
    await casesStore.fetchCaseEvidence(currentCaseId())
    if (isSelectedNodeTarget(target)) {
      await loadSelectedNodeEvidence(selectedNode.value)
    }
    evidenceTarget.value = null
  } catch (e) {
    evidenceError.value = e.response?.data?.detail || e.message
  }
}

function downloadEvidence(item) {
  window.open(api.evidenceDownloadUrl(currentCaseId(), item.id), '_blank')
}

function previewEvidence(item) {
  window.open(api.evidencePreviewUrl(currentCaseId(), item.id), '_blank')
}

async function deleteEvidence(item) {
  await casesStore.deleteCaseEvidence(currentCaseId(), item.id)
  if (selectedNode.value) {
    await loadSelectedNodeEvidence(selectedNode.value)
  }
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
            <span v-if="tab === 'evidence' && evidence.length" class="ml-1.5 badge badge-slate">{{ evidence.length }}</span>
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
          <div class="absolute top-3 left-3 z-20 flex flex-wrap items-center gap-2">
            <button class="btn-primary text-xs flex items-center gap-1.5" @click="openEntityModal()">
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M12 5v14M5 12h14"/>
              </svg>
              Add Node
            </button>
            <button
              v-if="selectedNode"
              class="btn-secondary text-xs"
              @click="openEntityModal(selectedNode)"
            >
              Add Connected
            </button>
            <button
              class="btn-secondary text-xs"
              :disabled="graphNodes.length < 2"
              @click="openRelationshipModal(selectedNode)"
            >
              Connect Nodes
            </button>
          </div>
          <!-- Loading overlay -->
          <div v-if="casesStore.loading" class="absolute inset-0 flex items-center justify-center z-10" style="background-color: var(--bg-primary)">
            <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
          </div>
          <!-- Empty state -->
          <div v-else-if="!caseGraph?.nodes?.length" class="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <svg class="h-12 w-12 opacity-20" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>
            </svg>
            <p class="text-sm" style="color: var(--text-muted)">No graph data yet. Add a manual node or start a scan.</p>
            <div class="flex items-center gap-2">
              <button class="btn-primary" @click="openEntityModal()">Add Manual Node</button>
              <button class="btn-secondary" @click="showScanModal = true">Add Scan</button>
            </div>
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
          :evidence-items="selectedNodeEvidence"
          :evidence-loading="selectedNodeEvidenceLoading"
          @close="closeSelectedNode"
          @scan-from-node="openScanFromNode"
          @attach-evidence="openEvidenceModal"
          @preview-evidence="previewEvidence"
          @download-evidence="downloadEvidence"
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

        <!-- Evidence tab -->
        <div v-if="activeTab === 'evidence'">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div>
              <h2 class="text-lg font-semibold" style="color: var(--text-primary)">Evidence</h2>
              <p class="text-sm" style="color: var(--text-muted)">Files, source URLs, and analyst observations for this case.</p>
            </div>
            <button class="btn-primary flex items-center gap-2" @click="openEvidenceModal()">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              Add Evidence
            </button>
          </div>

          <div v-if="evidence.length === 0" class="text-center py-12" style="color: var(--text-muted)">
            No evidence has been added yet.
          </div>

          <div v-else class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <div v-for="item in evidence" :key="item.id" class="card p-4 flex flex-col gap-3">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <h3 class="font-medium truncate" style="color: var(--text-primary)" :title="item.title">{{ item.title }}</h3>
                  <div class="flex flex-wrap gap-1.5 mt-1">
                    <span class="badge badge-blue">{{ item.evidence_type }}</span>
                    <span class="badge badge-slate">{{ item.source_type }}</span>
                    <span v-if="item.links?.length" class="badge badge-slate">{{ item.links.length }} link{{ item.links.length === 1 ? '' : 's' }}</span>
                  </div>
                </div>
                <button class="btn-ghost text-xs text-red-400 shrink-0" @click="deleteEvidence(item)">Delete</button>
              </div>

              <img
                v-if="item.thumbnail_url"
                :src="item.thumbnail_url"
                :alt="item.title"
                class="w-full h-36 object-cover rounded border"
                style="border-color: var(--border); background-color: var(--bg-primary)"
              />

              <p v-if="item.description" class="text-sm line-clamp-3" style="color: var(--text-secondary)">{{ item.description }}</p>
              <a v-if="item.source_url" :href="item.source_url" target="_blank" rel="noopener noreferrer" class="text-xs break-all text-blue-400">
                {{ item.source_url }}
              </a>

              <div class="text-xs space-y-1 mt-auto" style="color: var(--text-muted)">
                <p v-if="item.file_name" class="truncate" :title="item.file_name">{{ item.file_name }}</p>
                <p v-if="item.file_size">{{ Math.ceil(item.file_size / 1024) }} KB · {{ item.file_mime_type }}</p>
                <p v-if="item.file_sha256" class="font-mono truncate" :title="item.file_sha256">sha256 {{ item.file_sha256 }}</p>
                <p>Added {{ fmtDate(item.created_at) }}</p>
              </div>

              <div class="flex gap-2 pt-1">
                <button v-if="item.preview_url" class="btn-secondary text-xs" @click="previewEvidence(item)">Preview</button>
                <button v-if="item.download_url" class="btn-secondary text-xs" @click="downloadEvidence(item)">Download</button>
              </div>
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

  <!-- Manual entity modal -->
  <Teleport to="body">
    <div v-if="showEntityModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showEntityModal = false">
      <div class="card p-6 w-full max-w-lg mx-4">
        <h2 class="text-lg font-semibold mb-1" style="color: var(--text-primary)">
          {{ entityRelationNode ? 'Add Connected Node' : 'Add Manual Node' }}
        </h2>
        <p v-if="entityRelationNode" class="text-xs mb-4" style="color: var(--text-muted)">
          Connecting from {{ entityRelationNode.kind }}: {{ entityRelationNode.value }}
        </p>
        <form @submit.prevent="submitEntity" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Type</label>
              <select v-model="entityForm.type" class="input">
                <option value="person">Person</option>
                <option value="alias">Alias</option>
                <option value="username">Username</option>
                <option value="email">Email</option>
                <option value="phone">Phone</option>
                <option value="address">Address</option>
                <option value="location">Location</option>
                <option value="social_profile">Social Profile</option>
                <option value="company">Company</option>
                <option value="organization">Organization</option>
                <option value="domain">Domain</option>
                <option value="ip">IP Address</option>
                <option value="vehicle">Vehicle</option>
                <option value="document">Document</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Status</label>
              <select v-model="entityForm.verification_status" class="input">
                <option value="lead">Lead</option>
                <option value="needs_review">Needs Review</option>
                <option value="confirmed">Confirmed</option>
                <option value="rejected">Rejected</option>
                <option value="stale">Stale</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Label *</label>
            <input v-model="entityForm.label" class="input" placeholder="Short display name" required />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Value *</label>
            <input v-model="entityForm.value" class="input" placeholder="Name, email, phone, address, domain, or identifier" required />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Description</label>
            <textarea v-model="entityForm.description" class="input h-20 resize-none" placeholder="Analyst note or source context" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Confidence</label>
              <select v-model="entityForm.confidence" class="input">
                <option value="">Unknown</option>
                <option value="0.3">Low</option>
                <option value="0.6">Medium</option>
                <option value="0.9">High</option>
                <option value="1">Verified</option>
              </select>
            </div>
            <div v-if="entityRelationNode">
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Relationship</label>
              <input v-model="entityForm.relationship_type" class="input" placeholder="associated_with" />
            </div>
          </div>
          <div v-if="entityRelationNode">
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Relationship Label</label>
            <input v-model="entityForm.relationship_label" class="input" placeholder="Optional display label" />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn-secondary" @click="showEntityModal = false">Cancel</button>
            <button type="submit" class="btn-primary">{{ entityRelationNode ? 'Create Connected Node' : 'Create Node' }}</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>

  <!-- Manual relationship modal -->
  <Teleport to="body">
    <div v-if="showRelationshipModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showRelationshipModal = false">
      <div class="card p-6 w-full max-w-lg mx-4">
        <h2 class="text-lg font-semibold mb-4" style="color: var(--text-primary)">Connect Nodes</h2>
        <form @submit.prevent="submitRelationship" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Source *</label>
            <select v-model="relationshipForm.from_node_id" class="input" required>
              <option value="" disabled>Select source node</option>
              <option v-for="node in graphNodes" :key="`from-${node.id}`" :value="node.id">
                {{ node.kind }} · {{ node.label || node.value }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Target *</label>
            <select v-model="relationshipForm.to_node_id" class="input" required>
              <option value="" disabled>Select target node</option>
              <option v-for="node in graphNodes" :key="`to-${node.id}`" :value="node.id">
                {{ node.kind }} · {{ node.label || node.value }}
              </option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Relationship *</label>
              <input v-model="relationshipForm.relationship_type" class="input" placeholder="associated_with" required />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Status</label>
              <select v-model="relationshipForm.verification_status" class="input">
                <option value="lead">Lead</option>
                <option value="needs_review">Needs Review</option>
                <option value="confirmed">Confirmed</option>
                <option value="rejected">Rejected</option>
                <option value="stale">Stale</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Label</label>
              <input v-model="relationshipForm.label" class="input" placeholder="Optional label" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Confidence</label>
              <select v-model="relationshipForm.confidence" class="input">
                <option value="">Unknown</option>
                <option value="0.3">Low</option>
                <option value="0.6">Medium</option>
                <option value="0.9">High</option>
                <option value="1">Verified</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Description</label>
            <textarea v-model="relationshipForm.description" class="input h-20 resize-none" placeholder="Why these nodes are connected" />
          </div>
          <p v-if="relationshipForm.from_node_id && relationshipForm.from_node_id === relationshipForm.to_node_id" class="text-xs text-red-400">
            Source and target must be different nodes.
          </p>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn-secondary" @click="showRelationshipModal = false">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="relationshipForm.from_node_id === relationshipForm.to_node_id">Create Relationship</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>

  <!-- Evidence modal -->
  <Teleport to="body">
    <div v-if="showEvidenceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showEvidenceModal = false">
      <div class="card p-6 w-full max-w-lg mx-4">
        <h2 class="text-lg font-semibold mb-1" style="color: var(--text-primary)">Add Evidence</h2>
        <p v-if="evidenceTarget" class="text-xs mb-4" style="color: var(--text-muted)">
          Linking to {{ graphNodeLabel(evidenceTarget) }}
        </p>
        <form @submit.prevent="submitEvidence" class="space-y-4">
          <div class="grid grid-cols-3 gap-2">
            <label class="flex items-center gap-2 text-sm rounded border px-3 py-2 cursor-pointer"
              :style="{ borderColor: evidenceForm.mode === 'file' ? 'rgb(59 130 246)' : 'var(--border)', color: 'var(--text-secondary)' }">
              <input v-model="evidenceForm.mode" type="radio" value="file" />
              File
            </label>
            <label class="flex items-center gap-2 text-sm rounded border px-3 py-2 cursor-pointer"
              :style="{ borderColor: evidenceForm.mode === 'url' ? 'rgb(59 130 246)' : 'var(--border)', color: 'var(--text-secondary)' }">
              <input v-model="evidenceForm.mode" type="radio" value="url" />
              URL
            </label>
            <label class="flex items-center gap-2 text-sm rounded border px-3 py-2 cursor-pointer"
              :style="{ borderColor: evidenceForm.mode === 'note' ? 'rgb(59 130 246)' : 'var(--border)', color: 'var(--text-secondary)' }">
              <input v-model="evidenceForm.mode" type="radio" value="note" />
              Note
            </label>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Title *</label>
            <input v-model="evidenceForm.title" class="input" placeholder="Evidence title" required />
          </div>

          <div v-if="evidenceForm.mode === 'file'">
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">File *</label>
            <input class="input" type="file" required @change="onEvidenceFileChange" />
          </div>

          <div v-if="evidenceForm.mode !== 'note'">
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Source URL</label>
            <input v-model="evidenceForm.source_url" class="input" type="url" placeholder="https://example.com/source" :required="evidenceForm.mode === 'url'" />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Description</label>
            <textarea v-model="evidenceForm.description" class="input h-24 resize-none" placeholder="Context, collection notes, or observation" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Collected By</label>
              <input v-model="evidenceForm.collected_by" class="input" placeholder="Analyst name" />
            </div>
            <div v-if="evidenceTarget">
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Link Note</label>
              <input v-model="evidenceForm.relationship_note" class="input" placeholder="Why this supports the node" />
            </div>
          </div>

          <p v-if="evidenceError" class="text-sm text-red-400">{{ evidenceError }}</p>

          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn-secondary" @click="showEvidenceModal = false">Cancel</button>
            <button type="submit" class="btn-primary">Save Evidence</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>

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
