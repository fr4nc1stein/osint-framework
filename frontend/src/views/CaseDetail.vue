<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCasesStore } from '../stores/cases'
import GraphVisualization from '../components/GraphVisualization.vue'
import GraphSidebar from '../components/GraphSidebar.vue'
import GraphNodePanel from '../components/GraphNodePanel.vue'
import CaseMapView from '../components/CaseMapView.vue'
import CreateScanModal from '../components/CreateScanModal.vue'
import CaseEditModal from '../components/CaseEditModal.vue'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const casesStore = useCasesStore()

const caseId    = computed(() => route.params.id)
const activeTab = ref('scans')
const tabs      = ['scans', 'graph', 'leads', 'map', 'timeline', 'evidence', 'notes', 'reports']

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
const showTimelineModal = ref(false)
const showLocationModal = ref(false)
const entityRelationNode = ref(null)
const evidenceTarget = ref(null)
const timelineTarget = ref(null)
const locationTarget = ref(null)
const entityForm = ref(defaultEntityForm())
const relationshipForm = ref(defaultRelationshipForm())
const evidenceForm = ref(defaultEvidenceForm())
const timelineForm = ref(defaultTimelineForm())
const locationForm = ref(defaultLocationForm())
const evidenceFile = ref(null)
const evidenceError = ref('')
const timelineError = ref('')
const locationError = ref('')
const selectedNodeEvidence = ref([])
const selectedNodeEvidenceLoading = ref(false)
const leadStatusFilter = ref('open')
const leadTypeFilter = ref('all')
const leadMergeTargets = ref({})
const leadActionError = ref('')
const selectedLeadKeys = ref([])
const bulkLeadActionLoading = ref(false)

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
      selectedLeadKeys.value = []
      await loadCase(nextCaseId)
    }
  }
)

async function loadCase(id) {
  await casesStore.fetchCase(id)
  await casesStore.fetchCaseScans(id)
  await casesStore.fetchCaseGraph(id)
  await casesStore.fetchCaseLeads(id, { status: leadStatusFilter.value, lead_type: leadTypeFilter.value })
  await casesStore.fetchCaseEvidence(id)
  await casesStore.fetchCaseTimeline(id)
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
const timelineEvents = computed(() => casesStore.caseTimelineEvents)
const caseGraph   = computed(() => casesStore.caseGraph)
const caseMap     = computed(() => casesStore.caseMap)
const caseLeads   = computed(() => casesStore.caseLeads)
const nodeParentScanId = computed(() => resolveNodeParentScanId(scanFromNode.value))
const graphNodes = computed(() => caseGraph.value?.nodes ?? [])
const manualEntityOptions = computed(() => graphNodes.value.filter(node => node.graph_node_type === 'entity'))
const visibleLeads = computed(() => caseLeads.value?.items ?? [])
const selectedLeads = computed(() => visibleLeads.value.filter(lead => selectedLeadKeys.value.includes(leadKey(lead))))
const allVisibleLeadsSelected = computed(() => (
  visibleLeads.value.length > 0 && visibleLeads.value.every(lead => selectedLeadKeys.value.includes(leadKey(lead)))
))
const selectedLeadSummary = computed(() => {
  const counts = selectedLeads.value.reduce((acc, lead) => {
    acc[lead.target_type] = (acc[lead.target_type] || 0) + 1
    return acc
  }, {})
  return Object.entries(counts)
    .map(([type, count]) => `${count} ${type.replace(/_/g, ' ')}`)
    .join(', ')
})
const locationEntityOptions = computed(() => graphNodes.value.filter(node => (
  node.graph_node_type === 'entity' && ['address', 'location', 'office', 'company', 'organization', 'person', 'vehicle'].includes(node.kind)
)))

// Normalise case graph: the API returns scan_origins on nodes/edges,
// but GraphVisualization expects source/target not scan_origins on edges.
// The data shape already matches — just pass it through.

const timeline = computed(() => {
  const events = []
  for (const ev of timelineEvents.value) {
    events.push({
      id: ev.id,
      time: ev.occurred_at || ev.start_at || ev.created_at,
      type: ev.event_type,
      label: ev.title,
      detail: ev.description || ev.event_type.replace(/_/g, ' '),
      source: 'timeline_event',
      status: ev.verification_status,
      confidence: ev.confidence,
      links: ev.links || [],
      raw: ev,
    })
  }
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

const TIMELINE_ICON_MAP = {
  case: { icon: '📁', cls: 'bg-blue-500/20 text-blue-300' },
  scan: { icon: '🔍', cls: 'bg-amber-500/20 text-amber-300' },
  scan_done: { icon: '✅', cls: 'bg-emerald-500/20 text-emerald-300' },
  scan_failed: { icon: '❌', cls: 'bg-red-500/20 text-red-300' },
  report: { icon: '📄', cls: 'bg-purple-500/20 text-purple-300' },
  note: { icon: '📝', cls: 'bg-slate-500/20 text-slate-300' },
  evidence: { icon: '📎', cls: 'bg-cyan-500/20 text-cyan-300' },
  sighting: { icon: '👁', cls: 'bg-rose-500/20 text-rose-300' },
  address_observed: { icon: '⌂', cls: 'bg-lime-500/20 text-lime-300' },
  phone_observed: { icon: '☎', cls: 'bg-teal-500/20 text-teal-300' },
  email_observed: { icon: '@', cls: 'bg-yellow-500/20 text-yellow-300' },
  account_created: { icon: '+', cls: 'bg-indigo-500/20 text-indigo-300' },
  profile_updated: { icon: '↻', cls: 'bg-violet-500/20 text-violet-300' },
  domain_registered: { icon: '🌐', cls: 'bg-sky-500/20 text-sky-300' },
  breach_observed: { icon: '!', cls: 'bg-red-600/20 text-red-400' },
  scan_run: { icon: '🔎', cls: 'bg-amber-500/20 text-amber-300' },
  evidence_collected: { icon: '📎', cls: 'bg-cyan-500/20 text-cyan-300' },
  contact_attempt: { icon: '↗', cls: 'bg-orange-500/20 text-orange-300' },
  employment_observed: { icon: '▦', cls: 'bg-slate-500/20 text-slate-300' },
  travel_or_movement: { icon: '➜', cls: 'bg-emerald-500/20 text-emerald-300' },
  legal_event: { icon: '§', cls: 'bg-fuchsia-500/20 text-fuchsia-300' },
  custom: { icon: '•', cls: 'bg-slate-500/20 text-slate-300' },
}

function timelineIcon(ev) {
  return (TIMELINE_ICON_MAP[ev.type] || TIMELINE_ICON_MAP.custom).icon
}

function timelineIconClass(ev) {
  return (TIMELINE_ICON_MAP[ev.type] || TIMELINE_ICON_MAP.custom).cls
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
  if (tab === 'map' && casesStore.caseMapCaseId !== currentCaseId()) {
    await casesStore.fetchCaseMap(currentCaseId())
  }
  if (tab === 'evidence' && casesStore.caseEvidenceCaseId !== currentCaseId()) {
    await casesStore.fetchCaseEvidence(currentCaseId())
  }
  if (tab === 'timeline' && casesStore.caseTimelineEventsCaseId !== currentCaseId()) {
    await casesStore.fetchCaseTimeline(currentCaseId())
  }
  if (tab === 'leads' && casesStore.caseLeadsCaseId !== currentCaseId()) {
    await refreshLeads()
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
    address_text: '',
    latitude: '',
    longitude: '',
    location_precision: 'unknown',
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

function defaultTimelineForm() {
  return {
    title: '',
    description: '',
    event_type: 'custom',
    occurred_at: '',
    occurred_at_precision: 'unknown',
    location_entity_id: '',
    verification_status: 'lead',
    confidence: '0.6',
    created_by: '',
  }
}

function defaultLocationForm() {
  return {
    entity_id: '',
    label: '',
    address_text: '',
    latitude: '',
    longitude: '',
    location_precision: 'unknown',
    confidence: '0.6',
    verification_status: 'lead',
    location_note: '',
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

function timelineTargetType(target) {
  return target?.__timeline_target_type || target?.__evidence_target_type || graphNodeType(target)
}

function timelineTargetId(target) {
  return target?.__timeline_target_id || target?.__evidence_target_id || target?.id
}

function timelineTargetLabel(target) {
  if (!target) return ''
  return target.__timeline_label || target.__evidence_label || graphNodeLabel(target)
}

function mapTargetEntityId(target) {
  if (!target) return null
  if (target.target_type === 'entity') return target.target_id
  if (target.graph_node_type === 'entity') return target.id
  return null
}

function isManualLocationEntity(node) {
  return node?.graph_node_type === 'entity'
    && node?.source_type === 'manual'
    && ['address', 'location', 'office', 'company', 'organization', 'person', 'vehicle'].includes(node.kind)
}

async function resolveEntityNode(entityId) {
  if (!entityId) return null
  if (casesStore.caseGraphCaseId !== currentCaseId()) {
    await casesStore.fetchCaseGraph(currentCaseId())
  }
  return graphNodes.value.find(node => node.id === entityId) || null
}

async function openLocationEditor(target, seed = {}) {
  const entityId = mapTargetEntityId(target)
  const node = await resolveEntityNode(entityId)
  if (!isManualLocationEntity(node)) return

  const meta = node.meta || {}
  locationTarget.value = node
  locationForm.value = {
    entity_id: node.id,
    label: node.label || node.value,
    address_text: seed.address_text ?? meta.address_text ?? meta.address ?? node.value,
    latitude: seed.latitude ?? meta.latitude ?? meta.lat ?? '',
    longitude: seed.longitude ?? meta.longitude ?? meta.lon ?? meta.lng ?? '',
    location_precision: seed.location_precision ?? meta.location_precision ?? meta.precision ?? 'unknown',
    confidence: node.confidence == null ? '0.6' : String(node.confidence),
    verification_status: node.verification_status || 'lead',
    location_note: meta.location_note || '',
  }
  locationError.value = ''
  showLocationModal.value = true
}

async function openMapForNode(node) {
  if (!node) return
  selectedNode.value = null
  await switchTab('map')
}

async function submitLocation() {
  locationError.value = ''
  const node = locationTarget.value
  if (!node) return

  const lat = Number(locationForm.value.latitude)
  const lon = Number(locationForm.value.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
    locationError.value = 'Latitude must be -90 to 90 and longitude must be -180 to 180.'
    return
  }

  const properties = { ...(node.meta || {}) }
  properties.address_text = locationForm.value.address_text || node.value
  properties.latitude = lat
  properties.longitude = lon
  properties.location_precision = locationForm.value.location_precision || 'unknown'
  if (locationForm.value.location_note) {
    properties.location_note = locationForm.value.location_note
  } else {
    delete properties.location_note
  }

  const confidence = locationForm.value.confidence === '' ? null : Number(locationForm.value.confidence)
  await casesStore.updateCaseEntity(currentCaseId(), node.id, {
    properties,
    confidence,
    verification_status: locationForm.value.verification_status,
  })
  await casesStore.fetchCaseMap(currentCaseId())

  const updatedNode = graphNodes.value.find(item => item.id === node.id)
  if (selectedNode.value?.id === node.id && updatedNode) {
    selectedNode.value = updatedNode
  }

  showLocationModal.value = false
  locationTarget.value = null
}

function handleMarkerMoved(payload) {
  if (!payload?.marker) return
  openLocationEditor(payload.marker, {
    latitude: payload.latitude,
    longitude: payload.longitude,
    address_text: payload.marker.address_text,
    location_precision: payload.marker.precision,
  })
}

function mapActionTarget(marker) {
  if (!marker) return null
  return {
    id: marker.target_id,
    label: marker.label,
    value: marker.label,
    kind: marker.entity_type || marker.marker_type,
    __evidence_target_type: marker.target_type,
    __evidence_target_id: marker.target_id,
    __evidence_label: `map · ${marker.label}`,
    __timeline_target_type: marker.target_type,
    __timeline_target_id: marker.target_id,
    __timeline_label: `map · ${marker.label}`,
  }
}

async function openMapTarget(link) {
  if (!link) return
  if (['entity', 'indicator'].includes(link.target_type)) {
    if (casesStore.caseGraphCaseId !== currentCaseId()) {
      await casesStore.fetchCaseGraph(currentCaseId())
    }
    const node = graphNodes.value.find(item => item.id === link.target_id)
    if (node) {
      activeTab.value = 'graph'
      onNodeSelect(node)
    }
    return
  }
  if (link.target_type === 'evidence') {
    activeTab.value = 'evidence'
    return
  }
  if (link.target_type === 'timeline_event') {
    activeTab.value = 'timeline'
    return
  }
  if (link.target_type === 'scan') {
    router.push(`/scan/${link.target_id}`)
  }
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

function openEntityModal(connectedNode = null, defaults = {}) {
  entityRelationNode.value = connectedNode
  entityForm.value = { ...defaultEntityForm(), ...defaults }
  showEntityModal.value = true
}

function openMapEntityModal(defaults = {}) {
  openEntityModal(null, defaults)
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

  if (entityForm.value.address_text) payload.properties.address_text = entityForm.value.address_text
  if (entityForm.value.latitude !== '') payload.properties.latitude = Number(entityForm.value.latitude)
  if (entityForm.value.longitude !== '') payload.properties.longitude = Number(entityForm.value.longitude)
  if (entityForm.value.location_precision) payload.properties.location_precision = entityForm.value.location_precision

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
  if (activeTab.value === 'map') {
    await casesStore.fetchCaseMap(currentCaseId())
  }
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

async function refreshLeads() {
  await casesStore.fetchCaseLeads(currentCaseId(), {
    status: leadStatusFilter.value,
    lead_type: leadTypeFilter.value,
  })
  const visibleKeys = new Set(visibleLeads.value.map(lead => leadKey(lead)))
  selectedLeadKeys.value = selectedLeadKeys.value.filter(key => visibleKeys.has(key))
}

async function onLeadFiltersChanged() {
  selectedLeadKeys.value = []
  await refreshLeads()
}

function leadKey(lead) {
  return `${lead.target_type}:${lead.target_id}`
}

function isLeadSelected(lead) {
  return selectedLeadKeys.value.includes(leadKey(lead))
}

function toggleLeadSelection(lead) {
  const key = leadKey(lead)
  selectedLeadKeys.value = selectedLeadKeys.value.includes(key)
    ? selectedLeadKeys.value.filter(item => item !== key)
    : [...selectedLeadKeys.value, key]
}

function selectAllVisibleLeads() {
  selectedLeadKeys.value = allVisibleLeadsSelected.value
    ? []
    : visibleLeads.value.map(lead => leadKey(lead))
}

function clearSelectedLeads() {
  selectedLeadKeys.value = []
}

function leadBadgeClass(status) {
  return {
    lead: 'badge-blue',
    needs_review: 'badge-amber',
    follow_up: 'badge-purple',
    confirmed: 'badge-green',
    rejected: 'badge-red',
    stale: 'badge-slate',
  }[status] || 'badge-slate'
}

function leadTarget(lead) {
  return {
    id: lead.target_id,
    kind: lead.lead_type,
    label: lead.label,
    value: lead.value || lead.label,
    graph_node_type: lead.target_type === 'indicator' ? 'indicator' : 'entity',
    __evidence_target_type: lead.target_type,
    __evidence_target_id: lead.target_id,
    __evidence_label: `${lead.target_type} · ${lead.label}`,
    __timeline_target_type: lead.target_type,
    __timeline_target_id: lead.target_id,
    __timeline_label: `${lead.target_type} · ${lead.label}`,
  }
}

async function reviewLead(lead, action, extra = {}) {
  leadActionError.value = ''
  try {
    await casesStore.reviewCaseLead(currentCaseId(), lead.target_type, lead.target_id, {
      action,
      notes: extra.notes || null,
      merged_entity_id: extra.merged_entity_id || null,
    })
    selectedLeadKeys.value = selectedLeadKeys.value.filter(key => key !== leadKey(lead))
    await casesStore.fetchCaseGraph(currentCaseId())
    if (activeTab.value === 'map') await casesStore.fetchCaseMap(currentCaseId())
    await refreshLeads()
  } catch (e) {
    leadActionError.value = e.response?.data?.detail || e.message
  }
}

async function bulkReviewLeads(action) {
  if (!selectedLeads.value.length || bulkLeadActionLoading.value) return
  if (action === 'reject') {
    const ok = window.confirm(`Reject ${selectedLeads.value.length} selected lead${selectedLeads.value.length === 1 ? '' : 's'}? Rejected leads are hidden from the default graph.`)
    if (!ok) return
  }

  leadActionError.value = ''
  bulkLeadActionLoading.value = true
  try {
    const targets = [...selectedLeads.value]
    for (const lead of targets) {
      await casesStore.reviewCaseLead(currentCaseId(), lead.target_type, lead.target_id, { action })
    }
    selectedLeadKeys.value = []
    await casesStore.fetchCaseGraph(currentCaseId())
    if (activeTab.value === 'map') await casesStore.fetchCaseMap(currentCaseId())
    await refreshLeads()
  } catch (e) {
    leadActionError.value = e.response?.data?.detail || e.message
  } finally {
    bulkLeadActionLoading.value = false
  }
}

async function mergeLead(lead) {
  const mergedEntityId = leadMergeTargets.value[leadKey(lead)]
  if (!mergedEntityId) {
    leadActionError.value = 'Select a manual entity to merge into.'
    return
  }
  await reviewLead(lead, 'merge', { merged_entity_id: mergedEntityId })
}

async function openLeadInGraph(lead) {
  if (!['entity', 'indicator'].includes(lead.target_type)) return
  if (casesStore.caseGraphCaseId !== currentCaseId()) {
    await casesStore.fetchCaseGraph(currentCaseId())
  }
  const node = graphNodes.value.find(item => item.id === lead.target_id)
  if (node) {
    activeTab.value = 'graph'
    onNodeSelect(node)
  }
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

function openTimelineModal(target = null) {
  timelineTarget.value = target
  timelineForm.value = defaultTimelineForm()
  timelineError.value = ''
  if (target) {
    timelineForm.value.title = `Timeline event for ${timelineTargetLabel(target)}`
  }
  if (casesStore.caseGraphCaseId !== currentCaseId()) {
    casesStore.fetchCaseGraph(currentCaseId()).catch(() => {})
  }
  showTimelineModal.value = true
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
    if (activeTab.value === 'map') {
      await casesStore.fetchCaseMap(currentCaseId())
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

function timelineDateToIso(value) {
  if (!value) return null
  return new Date(value).toISOString()
}

async function submitTimelineEvent() {
  timelineError.value = ''
  const target = timelineTarget.value
  try {
    const confidence = timelineForm.value.confidence === '' ? null : Number(timelineForm.value.confidence)
    const payload = {
      title: timelineForm.value.title,
      description: timelineForm.value.description || null,
      event_type: timelineForm.value.event_type,
      occurred_at: timelineDateToIso(timelineForm.value.occurred_at),
      occurred_at_precision: timelineForm.value.occurred_at ? timelineForm.value.occurred_at_precision : 'unknown',
      verification_status: timelineForm.value.verification_status,
      confidence,
      source_type: 'manual',
      created_by: timelineForm.value.created_by || null,
      links: [],
    }
    if (timelineForm.value.location_entity_id) {
      payload.location_entity_id = timelineForm.value.location_entity_id
    }
    if (target) {
      payload.links.push({
        target_type: timelineTargetType(target),
        target_id: timelineTargetId(target),
      })
    }
    await casesStore.createCaseTimelineEvent(currentCaseId(), payload)
    showTimelineModal.value = false
    timelineTarget.value = null
    if (activeTab.value === 'map') {
      await casesStore.fetchCaseMap(currentCaseId())
    }
  } catch (e) {
    timelineError.value = e.response?.data?.detail || e.message
  }
}

async function deleteTimelineEvent(eventId) {
  await casesStore.deleteCaseTimelineEvent(currentCaseId(), eventId)
}

function scanTimelineTarget(scan) {
  return {
    id: scan.id,
    __timeline_target_type: 'scan',
    __timeline_target_id: scan.id,
    __timeline_label: `scan · ${scan.seed_value}`,
  }
}

function evidenceTimelineTarget(item) {
  return {
    id: item.id,
    __timeline_target_type: 'evidence',
    __timeline_target_id: item.id,
    __timeline_label: `evidence · ${item.title}`,
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
            <span v-if="tab === 'leads' && caseLeads?.counts?.open" class="ml-1.5 badge badge-amber">{{ caseLeads.counts.open }}</span>
            <span v-if="tab === 'map' && caseMap?.counts?.markers" class="ml-1.5 badge badge-green">{{ caseMap.counts.markers }}</span>
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
          @add-timeline-event="openTimelineModal"
          @preview-evidence="previewEvidence"
          @download-evidence="downloadEvidence"
          @edit-location="openLocationEditor"
          @open-map-location="openMapForNode"
        />
      </div>

      <!-- ── MAP TAB ───────────────────────────────────────── -->
      <div v-else-if="activeTab === 'map'" class="flex-1 min-h-0 overflow-hidden">
        <CaseMapView
          :map-data="caseMap"
          :loading="casesStore.loading"
          @open-target="openMapTarget"
          @add-evidence="openEvidenceModal(mapActionTarget($event))"
          @add-timeline="openTimelineModal(mapActionTarget($event))"
          @edit-location="openLocationEditor"
          @map-unmapped="openLocationEditor"
          @move-marker="handleMarkerMoved"
          @create-node="openMapEntityModal"
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
                <button class="btn-ghost text-xs shrink-0" @click.stop="openTimelineModal(scanTimelineTarget(s))">Timeline</button>
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
                <button class="btn-ghost text-xs shrink-0" @click.stop="openTimelineModal(scanTimelineTarget(child))">Timeline</button>
                <span class="text-xs shrink-0" style="color: var(--text-muted)">{{ fmtDate(child.created_at) }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- Leads tab -->
        <div v-if="activeTab === 'leads'" class="space-y-4">
          <div class="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 class="text-lg font-semibold" style="color: var(--text-primary)">Leads</h2>
              <p class="text-sm" style="color: var(--text-muted)">Review manual observations and scan-derived findings before treating them as facts.</p>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <select v-model="leadStatusFilter" class="input text-sm w-40" @change="onLeadFiltersChanged">
                <option value="open">Open</option>
                <option value="all">All</option>
                <option value="lead">Lead</option>
                <option value="needs_review">Needs Review</option>
                <option value="follow_up">Follow Up</option>
                <option value="confirmed">Confirmed</option>
                <option value="rejected">Rejected</option>
                <option value="stale">Stale</option>
              </select>
              <select v-model="leadTypeFilter" class="input text-sm w-40" @change="onLeadFiltersChanged">
                <option value="all">All Types</option>
                <option value="entity">Manual Entities</option>
                <option value="relationship">Relationships</option>
                <option value="indicator">Scan Indicators</option>
                <option value="graph_edge">Scan Edges</option>
                <option value="geolocation">Geolocations</option>
                <option value="timeline_event">Timeline Events</option>
              </select>
              <button class="btn-secondary text-sm" @click="refreshLeads">Refresh</button>
            </div>
          </div>

          <div class="grid gap-3 md:grid-cols-4">
            <div class="card p-3">
              <p class="text-xs" style="color: var(--text-muted)">Open</p>
              <p class="text-xl font-semibold" style="color: var(--text-primary)">{{ caseLeads?.counts?.open || 0 }}</p>
            </div>
            <div class="card p-3">
              <p class="text-xs" style="color: var(--text-muted)">Needs Review</p>
              <p class="text-xl font-semibold" style="color: var(--text-primary)">{{ caseLeads?.counts?.by_status?.needs_review || 0 }}</p>
            </div>
            <div class="card p-3">
              <p class="text-xs" style="color: var(--text-muted)">Follow Up</p>
              <p class="text-xl font-semibold" style="color: var(--text-primary)">{{ caseLeads?.counts?.by_status?.follow_up || 0 }}</p>
            </div>
            <div class="card p-3">
              <p class="text-xs" style="color: var(--text-muted)">Confirmed</p>
              <p class="text-xl font-semibold" style="color: var(--text-primary)">{{ caseLeads?.counts?.by_status?.confirmed || 0 }}</p>
            </div>
          </div>

          <p v-if="leadActionError" class="text-sm text-red-400">{{ leadActionError }}</p>

          <div
            v-if="caseLeads?.items?.length"
            class="sticky top-0 z-10 rounded-lg border p-3 flex flex-wrap items-center justify-between gap-3"
            style="border-color: var(--border); background-color: var(--bg-secondary)"
          >
            <label class="flex items-center gap-2 text-sm cursor-pointer" style="color: var(--text-secondary)">
              <input
                type="checkbox"
                :checked="allVisibleLeadsSelected"
                @change="selectAllVisibleLeads"
              />
              Select all visible
            </label>
            <div v-if="selectedLeads.length" class="flex flex-wrap items-center gap-2">
              <span class="badge badge-amber">{{ selectedLeads.length }} selected</span>
              <span v-if="selectedLeadSummary" class="text-xs" style="color: var(--text-muted)">{{ selectedLeadSummary }}</span>
              <button class="btn-secondary text-xs" :disabled="bulkLeadActionLoading" @click="bulkReviewLeads('confirm')">Confirm</button>
              <button class="btn-secondary text-xs" :disabled="bulkLeadActionLoading" @click="bulkReviewLeads('follow_up')">Follow Up</button>
              <button class="btn-secondary text-xs" :disabled="bulkLeadActionLoading" @click="bulkReviewLeads('stale')">Stale</button>
              <button class="btn-secondary text-xs text-red-300" :disabled="bulkLeadActionLoading" @click="bulkReviewLeads('reject')">Reject</button>
              <button class="btn-ghost text-xs" :disabled="bulkLeadActionLoading" @click="clearSelectedLeads">Clear</button>
            </div>
          </div>

          <div v-if="!caseLeads || casesStore.loading" class="flex items-center justify-center h-24">
            <div class="h-7 w-7 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
          </div>
          <div v-else-if="caseLeads.items.length === 0" class="text-center py-12" style="color: var(--text-muted)">
            No leads match the current filters.
          </div>
          <div v-else class="space-y-3">
            <div v-for="lead in caseLeads.items" :key="lead.id" class="card p-4">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div class="min-w-0 flex-1 flex gap-3">
                  <input
                    type="checkbox"
                    class="mt-1 shrink-0"
                    :checked="isLeadSelected(lead)"
                    @change="toggleLeadSelection(lead)"
                  />
                  <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <h3 class="font-medium break-words" style="color: var(--text-primary)">{{ lead.label }}</h3>
                    <span class="badge badge-blue">{{ lead.lead_type }}</span>
                    <span class="badge badge-slate">{{ lead.target_type }}</span>
                    <span class="badge" :class="leadBadgeClass(lead.review_status)">{{ lead.review_status.replace(/_/g, ' ') }}</span>
                  </div>
                  <p v-if="lead.value && lead.value !== lead.label" class="text-sm mt-1 break-all" style="color: var(--text-secondary)">{{ lead.value }}</p>
                  <p v-if="lead.description" class="text-sm mt-1" style="color: var(--text-secondary)">{{ lead.description }}</p>
                  <div class="flex flex-wrap gap-1.5 mt-2">
                    <span class="badge badge-slate">{{ lead.source_type }}</span>
                    <span v-if="lead.source_module" class="badge badge-slate">{{ lead.source_module }}</span>
                    <span v-if="lead.confidence != null" class="badge badge-slate">{{ Math.round(lead.confidence * 100) }}%</span>
                    <span v-if="lead.scan_origins?.length" class="badge badge-amber">{{ lead.scan_origins.length }} scan{{ lead.scan_origins.length === 1 ? '' : 's' }}</span>
                    <span v-if="lead.promoted_entity_id" class="badge badge-green">promoted</span>
                    <span v-if="lead.merged_entity_id" class="badge badge-green">merged</span>
                  </div>
                  <p v-if="lead.notes" class="text-xs mt-2" style="color: var(--text-muted)">{{ lead.notes }}</p>
                  </div>
                </div>
                <p class="text-xs shrink-0" style="color: var(--text-muted)">{{ lead.created_at ? fmtDate(lead.created_at) : '' }}</p>
              </div>

              <div class="flex flex-wrap items-center gap-2 mt-4">
                <button class="btn-secondary text-xs" @click="reviewLead(lead, 'confirm')">Confirm</button>
                <button class="btn-secondary text-xs" @click="reviewLead(lead, 'follow_up')">Follow Up</button>
                <button class="btn-secondary text-xs text-red-300" @click="reviewLead(lead, 'reject')">Reject</button>
                <button v-if="lead.target_type === 'indicator'" class="btn-secondary text-xs" @click="reviewLead(lead, 'promote')">Promote Node</button>
                <button v-if="['entity','indicator'].includes(lead.target_type)" class="btn-secondary text-xs" @click="openLeadInGraph(lead)">Graph</button>
                <button class="btn-secondary text-xs" @click="openEvidenceModal(leadTarget(lead))">Evidence</button>
                <button class="btn-secondary text-xs" @click="openTimelineModal(leadTarget(lead))">Timeline</button>
              </div>

              <div v-if="lead.target_type === 'indicator' && manualEntityOptions.length" class="mt-3 flex flex-wrap items-center gap-2">
                <select v-model="leadMergeTargets[leadKey(lead)]" class="input text-xs max-w-sm">
                  <option value="">Merge into manual entity...</option>
                  <option v-for="node in manualEntityOptions" :key="node.id" :value="node.id">
                    {{ node.kind }} · {{ node.label || node.value }}
                  </option>
                </select>
                <button class="btn-secondary text-xs" @click="mergeLead(lead)">Merge</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Timeline tab -->
        <div v-if="activeTab === 'timeline'" class="space-y-3">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div>
              <h2 class="text-lg font-semibold" style="color: var(--text-primary)">Timeline</h2>
              <p class="text-sm" style="color: var(--text-muted)">Manual investigation events plus case activity.</p>
            </div>
            <button class="btn-primary flex items-center gap-2" @click="openTimelineModal()">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              Add Event
            </button>
          </div>

          <div v-if="timeline.length === 0" class="flex items-center justify-center h-24">
            <p style="color: var(--text-muted)">No activity yet.</p>
          </div>
          <div v-for="(ev, i) in timeline" :key="i" class="flex gap-4 items-start">
            <div class="flex flex-col items-center">
              <div class="h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                :class="timelineIconClass(ev)">
                {{ timelineIcon(ev) }}
              </div>
              <div v-if="i < timeline.length - 1" class="w-0.5 flex-1 my-1" style="background-color: var(--border)"></div>
            </div>
            <div class="pb-4">
              <p class="text-sm font-medium" style="color: var(--text-primary)">{{ ev.label }}</p>
              <p class="text-sm" style="color: var(--text-secondary)">{{ ev.detail }}</p>
              <div class="flex flex-wrap gap-1.5 mt-1">
                <span v-if="ev.source === 'timeline_event'" class="badge badge-blue">{{ ev.type.replace(/_/g, ' ') }}</span>
                <span v-if="ev.status" class="badge badge-slate">{{ ev.status.replace(/_/g, ' ') }}</span>
                <span v-if="ev.links?.length" class="badge badge-slate">{{ ev.links.length }} link{{ ev.links.length === 1 ? '' : 's' }}</span>
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <p class="text-xs" style="color: var(--text-muted)">{{ fmtDate(ev.time) }}</p>
                <button v-if="ev.source === 'timeline_event'" class="btn-ghost text-xs text-red-400" @click="deleteTimelineEvent(ev.id)">Delete</button>
              </div>
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
                <button class="btn-secondary text-xs" @click="openTimelineModal(evidenceTimelineTarget(item))">Timeline</button>
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
                <option value="office">Office</option>
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
                <option value="follow_up">Follow Up</option>
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
          <div v-if="['address', 'location', 'office', 'company', 'organization', 'person', 'vehicle'].includes(entityForm.type)" class="grid grid-cols-2 gap-3">
            <div class="col-span-2">
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Map Label</label>
              <input v-model="entityForm.address_text" class="input" placeholder="Address, place name, or location note" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Latitude</label>
              <input v-model="entityForm.latitude" class="input" type="number" step="any" min="-90" max="90" placeholder="14.5995" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Longitude</label>
              <input v-model="entityForm.longitude" class="input" type="number" step="any" min="-180" max="180" placeholder="120.9842" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Location Precision</label>
              <select v-model="entityForm.location_precision" class="input">
                <option value="exact">Exact</option>
                <option value="building">Building</option>
                <option value="street">Street</option>
                <option value="city">City</option>
                <option value="region">Region</option>
                <option value="country">Country</option>
                <option value="ip_geo_approximate">IP Geo Approximate</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
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

  <!-- Location modal -->
  <Teleport to="body">
    <div v-if="showLocationModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showLocationModal = false">
      <div class="card p-6 w-full max-w-lg mx-4">
        <h2 class="text-lg font-semibold mb-1" style="color: var(--text-primary)">Location</h2>
        <p v-if="locationTarget" class="text-xs mb-4" style="color: var(--text-muted)">
          {{ locationTarget.kind }} · {{ locationTarget.label || locationTarget.value }}
        </p>
        <form @submit.prevent="submitLocation" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Map Label</label>
            <input v-model="locationForm.address_text" class="input" placeholder="Address, place name, or location note" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Latitude *</label>
              <input v-model="locationForm.latitude" class="input" type="number" step="any" min="-90" max="90" required />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Longitude *</label>
              <input v-model="locationForm.longitude" class="input" type="number" step="any" min="-180" max="180" required />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Precision</label>
              <select v-model="locationForm.location_precision" class="input">
                <option value="exact">Exact</option>
                <option value="building">Building</option>
                <option value="street">Street</option>
                <option value="city">City</option>
                <option value="region">Region</option>
                <option value="country">Country</option>
                <option value="ip_geo_approximate">IP Geo Approximate</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Status</label>
              <select v-model="locationForm.verification_status" class="input">
                <option value="lead">Lead</option>
                <option value="needs_review">Needs Review</option>
                <option value="follow_up">Follow Up</option>
                <option value="confirmed">Confirmed</option>
                <option value="rejected">Rejected</option>
                <option value="stale">Stale</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Confidence</label>
            <select v-model="locationForm.confidence" class="input">
              <option value="">Unknown</option>
              <option value="0.3">Low</option>
              <option value="0.6">Medium</option>
              <option value="0.9">High</option>
              <option value="1">Verified</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Location Note</label>
            <textarea v-model="locationForm.location_note" class="input h-20 resize-none" placeholder="Evidence, source, or analyst context" />
          </div>

          <p v-if="locationError" class="text-sm text-red-400">{{ locationError }}</p>

          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn-secondary" @click="showLocationModal = false">Cancel</button>
            <button type="submit" class="btn-primary">Save Location</button>
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
                <option value="follow_up">Follow Up</option>
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

  <!-- Timeline modal -->
  <Teleport to="body">
    <div v-if="showTimelineModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showTimelineModal = false">
      <div class="card p-6 w-full max-w-lg mx-4">
        <h2 class="text-lg font-semibold mb-1" style="color: var(--text-primary)">Add Timeline Event</h2>
        <p v-if="timelineTarget" class="text-xs mb-4" style="color: var(--text-muted)">
          Linking to {{ timelineTargetLabel(timelineTarget) }}
        </p>
        <form @submit.prevent="submitTimelineEvent" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Title *</label>
            <input v-model="timelineForm.title" class="input" placeholder="Observed address, account activity, contact attempt..." required />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Type</label>
              <select v-model="timelineForm.event_type" class="input">
                <option value="custom">Custom</option>
                <option value="sighting">Sighting</option>
                <option value="address_observed">Address Observed</option>
                <option value="phone_observed">Phone Observed</option>
                <option value="email_observed">Email Observed</option>
                <option value="account_created">Account Created</option>
                <option value="profile_updated">Profile Updated</option>
                <option value="domain_registered">Domain Registered</option>
                <option value="breach_observed">Breach Observed</option>
                <option value="scan_run">Scan Run</option>
                <option value="evidence_collected">Evidence Collected</option>
                <option value="contact_attempt">Contact Attempt</option>
                <option value="employment_observed">Employment Observed</option>
                <option value="travel_or_movement">Travel or Movement</option>
                <option value="legal_event">Legal Event</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Status</label>
              <select v-model="timelineForm.verification_status" class="input">
                <option value="lead">Lead</option>
                <option value="needs_review">Needs Review</option>
                <option value="follow_up">Follow Up</option>
                <option value="confirmed">Confirmed</option>
                <option value="rejected">Rejected</option>
                <option value="stale">Stale</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Occurred At</label>
              <input v-model="timelineForm.occurred_at" class="input" type="datetime-local" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Precision</label>
              <select v-model="timelineForm.occurred_at_precision" class="input">
                <option value="exact">Exact</option>
                <option value="date">Date</option>
                <option value="month">Month</option>
                <option value="year">Year</option>
                <option value="approximate">Approximate</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
          </div>

          <div v-if="locationEntityOptions.length">
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Location</label>
            <select v-model="timelineForm.location_entity_id" class="input">
              <option value="">No location</option>
              <option v-for="node in locationEntityOptions" :key="node.id" :value="node.id">
                {{ node.kind }} · {{ node.label || node.value }}
              </option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Confidence</label>
              <select v-model="timelineForm.confidence" class="input">
                <option value="">Unknown</option>
                <option value="0.3">Low</option>
                <option value="0.6">Medium</option>
                <option value="0.9">High</option>
                <option value="1">Verified</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Created By</label>
              <input v-model="timelineForm.created_by" class="input" placeholder="Analyst name" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Description</label>
            <textarea v-model="timelineForm.description" class="input h-24 resize-none" placeholder="What happened, how it was observed, and why it matters" />
          </div>

          <p v-if="timelineError" class="text-sm text-red-400">{{ timelineError }}</p>

          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn-secondary" @click="showTimelineModal = false">Cancel</button>
            <button type="submit" class="btn-primary">Save Event</button>
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
