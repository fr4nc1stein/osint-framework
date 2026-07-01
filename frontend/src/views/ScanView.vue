<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useScansStore } from '../stores/scans'
import { api } from '../api/client'
import GraphVisualization from '../components/GraphVisualization.vue'
import GraphSidebar from '../components/GraphSidebar.vue'
import GraphNodePanel from '../components/GraphNodePanel.vue'
import CreateScanModal from '../components/CreateScanModal.vue'

const route = useRoute()
const router = useRouter()
const scansStore = useScansStore()

const scan       = computed(() => scansStore.currentScan)
const loading    = computed(() => scansStore.loading)

const graphData      = ref(null)
const events         = ref([])
const ws             = ref(null)
const activeTab      = ref('graph')
const showExport     = ref(false)
const selectedNode   = ref(null)
const showScanModal  = ref(false)
const scanFromNode   = ref(null)

const tabs = [
  { id: 'graph',   label: 'Graph'   },
  { id: 'events',  label: 'Events'  },
  { id: 'details', label: 'Details' },
]

const statusBadge = {
  queued: 'badge-slate',
  running: 'badge-blue',
  completed: 'badge-green',
  partial: 'badge-amber',
  failed: 'badge-red',
  error: 'badge-red',
}

function fmtTime(ts) { return new Date(ts).toLocaleTimeString() }

async function loadGraph() {
  try {
    const { data } = await api.getScanGraph(route.params.id)
    graphData.value = data.graph
  } catch {}
}

function connectWS() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws.value = new WebSocket(`${proto}//${window.location.host}/ws/scan/${route.params.id}`)
  ws.value.onmessage = (e) => {
    const data = JSON.parse(e.data)
    events.value.unshift({ ...data, timestamp: Date.now() })
    if (data.type === 'module_complete' || data.type === 'scan_complete') {
      scansStore.fetchScan(route.params.id)
      loadGraph()
    }
  }
  ws.value.onerror = () => {}
}

function closeExport(e) {
  if (!e.target.closest('.export-menu')) showExport.value = false
}

function onNodeSelect(node) {
  selectedNode.value = node
}

function openScanFromNode(node) {
  scanFromNode.value = node
  showScanModal.value = true
}

async function exportScan(format) {
  showExport.value = false
  try {
    let response, filename
    if (format === 'json') {
      response = await api.exportJSON(route.params.id); filename = `scan_${route.params.id}.json`
    } else if (format === 'csv') {
      response = await api.exportCSV(route.params.id, 'edges'); filename = `scan_${route.params.id}_edges.csv`
    } else {
      response = await api.exportGraphML(route.params.id); filename = `scan_${route.params.id}.graphml`
    }
    const url = URL.createObjectURL(new Blob([response.data]))
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  } catch {}
}

onMounted(async () => {
  await scansStore.fetchScan(route.params.id)
  await loadGraph()
  connectWS()
  document.addEventListener('click', closeExport)
})

onUnmounted(() => {
  ws.value?.close()
  document.removeEventListener('click', closeExport)
})
</script>

<template>
  <div class="h-full flex flex-col overflow-hidden">

    <!-- Loading -->
    <div v-if="loading && !scan" class="flex items-center justify-center h-full">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
    </div>

    <template v-else-if="scan">

      <!-- ── Top bar ─────────────────────────────────────────── -->
      <div class="shrink-0 flex items-center gap-4 px-5 py-3 border-b" style="background-color: var(--bg-secondary); border-color: var(--border)">
        <button class="flex items-center gap-1 btn-ghost text-sm shrink-0" @click="router.push('/scans')">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
          Scans
        </button>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <h1 class="font-bold text-base truncate" style="color: var(--text-primary)">{{ scan.seed_value }}</h1>
            <span class="badge badge-blue text-[10px] shrink-0">{{ scan.seed_kind }}</span>
            <span class="badge shrink-0" :class="statusBadge[scan.status] || 'badge-slate'">{{ scan.status }}</span>
          </div>
        </div>

        <!-- Stat pills -->
        <div class="hidden md:flex items-center gap-3 shrink-0 text-xs font-mono">
          <span style="color: var(--text-muted)">
            <span class="text-blue-400 font-semibold">{{ graphData?.nodes?.length ?? 0 }}</span> nodes
          </span>
          <span style="color: var(--text-muted)">
            <span class="text-purple-400 font-semibold">{{ graphData?.edges?.length ?? 0 }}</span> edges
          </span>
          <span style="color: var(--text-muted)">
            <span class="text-emerald-400 font-semibold">{{ scan.progress }}/{{ scan.total_modules }}</span> modules
          </span>
        </div>

        <!-- Tab switcher -->
        <div class="flex items-center gap-0.5 rounded-md border overflow-hidden shrink-0"
          style="border-color: var(--border); background-color: var(--bg-primary)">
          <button v-for="tab in tabs" :key="tab.id"
            class="px-3 py-1.5 text-xs font-medium transition-all"
            :style="activeTab === tab.id
              ? 'background-color: var(--accent); color: #fff'
              : 'color: var(--text-secondary)'"
            @click="activeTab = tab.id">
            {{ tab.label }}
          </button>
        </div>

        <!-- Export -->
        <div class="relative export-menu shrink-0">
          <button class="btn-secondary flex items-center gap-1.5 text-sm" @click.stop="showExport = !showExport">
            Export
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
          </button>
          <div v-if="showExport" class="absolute right-0 mt-1 w-44 rounded-lg border shadow-lg z-20 overflow-hidden"
            style="background-color: var(--card-bg); border-color: var(--border)">
            <button class="w-full text-left px-4 py-2.5 text-sm hover:brightness-110 transition-all" style="color: var(--text-primary)" @click="exportScan('json')">Export JSON</button>
            <button class="w-full text-left px-4 py-2.5 text-sm hover:brightness-110 transition-all" style="color: var(--text-primary)" @click="exportScan('csv')">Export CSV</button>
            <button class="w-full text-left px-4 py-2.5 text-sm hover:brightness-110 transition-all" style="color: var(--text-primary)" @click="exportScan('graphml')">Export GraphML</button>
          </div>
        </div>
      </div>

      <!-- ── Graph tab: 3-column ────────────────────────────── -->
      <div v-if="activeTab === 'graph'" class="flex-1 flex overflow-hidden">
        <!-- Left sidebar: grouped indicators -->
        <GraphSidebar
          :graph-data="graphData"
          :seed-value="scan.seed_value"
          :seed-kind="scan.seed_kind"
          @node:select="onNodeSelect"
        />

        <!-- Center: graph canvas -->
        <div class="flex-1 overflow-hidden">
          <GraphVisualization
            :graph-data="graphData"
            @node:select="onNodeSelect"
          />
        </div>

        <!-- Right: node detail panel -->
        <GraphNodePanel
          :node="selectedNode"
          :graph-data="graphData"
          @close="selectedNode = null"
          @scan-from-node="openScanFromNode"
        />
      </div>

      <!-- ── Events tab ─────────────────────────────────────── -->
      <div v-if="activeTab === 'events'" class="flex-1 overflow-y-auto p-5">
        <div v-if="events.length === 0" class="flex items-center justify-center h-40">
          <p class="text-sm" style="color: var(--text-muted)">Events appear in real-time as the scan runs.</p>
        </div>
        <div v-else class="space-y-2">
          <div v-for="(ev, i) in events" :key="i" class="rounded-lg p-3" style="background-color: var(--bg-secondary); border: 1px solid var(--border)">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-medium" style="color: var(--text-primary)">{{ ev.type }}</span>
              <span class="text-xs" style="color: var(--text-muted)">{{ fmtTime(ev.timestamp) }}</span>
            </div>
            <pre class="text-xs overflow-x-auto whitespace-pre-wrap" style="color: var(--text-secondary)">{{ JSON.stringify(ev, null, 2) }}</pre>
          </div>
        </div>
      </div>

      <!-- ── Details tab ────────────────────────────────────── -->
      <div v-if="activeTab === 'details'" class="flex-1 overflow-y-auto p-5">
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div v-for="[label, value] in [
            ['Scan ID',     scan.id],
            ['Status',      scan.status],
            ['Target',      scan.seed_value],
            ['Type',        scan.seed_kind],
            ['Case',        scan.case_id || 'None'],
            ['Parent Scan', scan.parent_scan_id || 'None'],
            ['Created',     new Date(scan.created_at).toLocaleString()],
            ['Started',     scan.started_at ? new Date(scan.started_at).toLocaleString() : '—'],
            ['Finished',    scan.finished_at ? new Date(scan.finished_at).toLocaleString() : '—'],
            ['Modules',     scan.modules.join(', ')],
          ]" :key="label">
            <dt class="text-xs font-medium" style="color: var(--text-muted)">{{ label }}</dt>
            <dd class="mt-0.5 text-sm font-mono break-all" style="color: var(--text-primary)">{{ value }}</dd>
          </div>
        </dl>
      </div>
    </template>
  </div>

  <!-- Scan-from-node modal -->
  <CreateScanModal
    v-if="showScanModal && scanFromNode"
    :default-target="scanFromNode.value"
    :default-kind="scanFromNode.kind"
    :default-case-id="scan?.case_id"
    :parent-scan-id="route.params.id"
    @close="showScanModal = false; scanFromNode = null"
    @created="() => { showScanModal = false; scanFromNode = null }"
  />
</template>
