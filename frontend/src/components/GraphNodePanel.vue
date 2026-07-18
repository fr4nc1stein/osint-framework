<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  node:      { type: Object, default: null },
  graphData: { type: Object, default: null },
  evidenceItems: { type: Array, default: () => [] },
  evidenceLoading: { type: Boolean, default: false },
})

const emit = defineEmits([
  'close',
  'edit-node',
  'scan-from-node',
  'attach-evidence',
  'add-timeline-event',
  'preview-evidence',
  'download-evidence',
  'edit-location',
  'open-map-location',
])

const copied = ref(false)

const edges = computed(() => props.graphData?.edges ?? [])
const nodes = computed(() => props.graphData?.nodes ?? [])

const connectedEdges = computed(() => {
  if (!props.node) return []
  return edges.value.filter(e => e.source === props.node.id || e.target === props.node.id)
})

function linkedNode(edge) {
  const id = edge.source === props.node.id ? edge.target : edge.source
  return nodes.value.find(n => n.id === id)
}

function confColor(c) {
  if (c >= 0.85) return 'text-emerald-400'
  if (c >= 0.6)  return 'text-amber-400'
  return 'text-red-400'
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function fmtBytes(size) {
  if (!size) return ''
  if (size < 1024 * 1024) return `${Math.ceil(size / 1024)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

async function copyValue() {
  await navigator.clipboard.writeText(props.node.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}

const META_SYSTEM_KEYS = new Set(['source_type', 'verification_status', 'graph_node_type'])

const displayMeta = computed(() => {
  if (!props.node?.meta) return {}
  return Object.fromEntries(
    Object.entries(props.node.meta).filter(([k]) => !META_SYSTEM_KEYS.has(k))
  )
})

const locationCapableKinds = new Set(['address', 'location', 'office', 'company', 'organization', 'person', 'vehicle'])

const isManualEntity = computed(() => props.node?.graph_node_type === 'entity')
const canEditLocation = computed(() => isManualEntity.value && locationCapableKinds.has(props.node?.kind))
const locationMeta = computed(() => props.node?.meta || {})
const latitude = computed(() => locationMeta.value.latitude ?? locationMeta.value.lat ?? '')
const longitude = computed(() => locationMeta.value.longitude ?? locationMeta.value.lon ?? locationMeta.value.lng ?? '')
const hasLocation = computed(() => latitude.value !== '' && longitude.value !== '' && latitude.value != null && longitude.value != null)
const locationPrecision = computed(() => locationMeta.value.location_precision || locationMeta.value.precision || 'unknown')
const locationLabel = computed(() => locationMeta.value.address_text || locationMeta.value.address || props.node?.label || props.node?.value)

const KIND_BADGE = {
  domain:       'bg-blue-500/20 text-blue-300',
  person:       'bg-indigo-500/20 text-indigo-300',
  alias:        'bg-purple-500/20 text-purple-300',
  subdomain:    'bg-sky-500/20 text-sky-300',
  hostname:     'bg-violet-500/20 text-violet-300',
  ip:           'bg-emerald-500/20 text-emerald-300',
  nameserver:   'bg-amber-500/20 text-amber-300',
  server:       'bg-teal-500/20 text-teal-300',
  asn:          'bg-indigo-500/20 text-indigo-300',
  isp:          'bg-slate-500/20 text-slate-300',
  port:         'bg-cyan-500/20 text-cyan-300',
  service:      'bg-cyan-500/20 text-cyan-300',
  email:        'bg-amber-500/20 text-amber-300',
  address:      'bg-rose-500/20 text-rose-300',
  office:       'bg-rose-500/20 text-rose-300',
  phone:        'bg-purple-500/20 text-purple-300',
  username:     'bg-purple-500/20 text-purple-300',
  social_profile:'bg-yellow-500/20 text-yellow-300',
  company:      'bg-slate-500/20 text-slate-300',
  organization: 'bg-slate-500/20 text-slate-300',
  registrar:    'bg-slate-500/20 text-slate-300',
  profile_url:  'bg-yellow-500/20 text-yellow-300',
  url:          'bg-yellow-500/20 text-yellow-300',
  reputation:   'bg-orange-500/20 text-orange-300',
  category:     'bg-teal-500/20 text-teal-300',
  breach:       'bg-red-500/20 text-red-300',
  threat:       'bg-red-600/20 text-red-400',
  cve:          'bg-orange-600/20 text-orange-400',
  location:     'bg-rose-500/20 text-rose-300',
  vehicle:      'bg-emerald-500/20 text-emerald-300',
  document:     'bg-slate-500/20 text-slate-300',
}
</script>

<template>
  <aside
    v-if="node"
    class="w-72 shrink-0 flex flex-col border-l overflow-hidden animate-slide-in"
    style="background-color: var(--bg-sidebar); border-color: var(--border)"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b shrink-0" style="border-color: var(--border)">
      <div class="flex items-center gap-2 min-w-0">
        <span class="badge text-[10px] shrink-0" :class="KIND_BADGE[node.kind] || 'bg-slate-500/20 text-slate-300'">
          {{ node.kind.replace(/_/g, ' ') }}
        </span>
        <span class="text-sm font-semibold truncate" style="color: var(--text-primary)" :title="node.value">
          {{ node.label || node.value }}
        </span>
      </div>
      <button class="shrink-0 p-1 rounded transition-all hover:bg-slate-700" style="color: var(--text-muted)" @click="emit('close')">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path d="M6 18 18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <div class="flex-1 overflow-y-auto">
      <!-- Value + copy -->
      <div class="px-4 py-3 border-b" style="border-color: var(--border)">
        <p class="text-xs mb-1" style="color: var(--text-muted)">Value</p>
        <div class="flex items-start gap-2">
          <p class="text-xs font-mono break-all flex-1" style="color: var(--text-primary)">{{ node.value }}</p>
          <button class="shrink-0 p-1 rounded transition-all hover:bg-slate-700" :title="copied ? 'Copied!' : 'Copy'"
            @click="copyValue">
            <svg v-if="!copied" class="h-3.5 w-3.5" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6">
              <path d="M8 7.5V6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-1.5M6 7.5h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z"/>
            </svg>
            <svg v-else class="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="m5 13 4 4L19 7"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Metadata -->
      <div class="px-4 py-3 border-b grid grid-cols-1 gap-2" style="border-color: var(--border)">
        <div v-if="node.confidence != null">
          <p class="text-xs mb-0.5" style="color: var(--text-muted)">Confidence</p>
          <div class="flex items-center gap-2">
            <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background-color: var(--bg-tertiary)">
              <div class="h-full rounded-full transition-all"
                :class="node.confidence >= 0.85 ? 'bg-emerald-500' : node.confidence >= 0.6 ? 'bg-amber-500' : 'bg-red-500'"
                :style="`width: ${Math.round(node.confidence * 100)}%`" />
            </div>
            <span class="text-xs font-mono shrink-0" :class="confColor(node.confidence)">
              {{ Math.round(node.confidence * 100) }}%
            </span>
          </div>
        </div>
        <div v-if="Object.keys(displayMeta).length">
          <p class="text-xs mb-1" style="color: var(--text-muted)">Metadata</p>
          <div class="space-y-0.5">
            <div v-for="(val, key) in displayMeta" :key="key" class="flex gap-2">
              <span class="text-[10px] font-mono shrink-0" style="color: var(--text-muted)">{{ key }}</span>
              <span class="text-[10px] font-mono break-all" style="color: var(--text-secondary)">{{ val }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Location -->
      <div v-if="canEditLocation" class="px-4 py-3 border-b" style="border-color: var(--border)">
        <div class="flex items-center justify-between gap-2 mb-2">
          <p class="text-xs font-semibold uppercase tracking-wider" style="color: var(--text-muted)">
            Location
          </p>
          <span class="badge text-[10px]" :class="hasLocation ? 'badge-green' : 'badge-slate'">
            {{ hasLocation ? 'Mapped' : 'Unmapped' }}
          </span>
        </div>

        <div v-if="hasLocation" class="rounded-lg border p-2.5 space-y-2" style="border-color: var(--border); background-color: var(--bg-primary)">
          <div>
            <p class="text-xs font-medium truncate" style="color: var(--text-primary)" :title="locationLabel">
              {{ locationLabel }}
            </p>
            <p class="text-[10px] font-mono mt-1" style="color: var(--text-muted)">
              {{ Number(latitude).toFixed(5) }}, {{ Number(longitude).toFixed(5) }}
            </p>
          </div>
          <div class="flex flex-wrap gap-1.5">
            <span class="badge badge-slate text-[9px]">{{ locationPrecision }}</span>
            <span v-if="node.verification_status" class="badge badge-blue text-[9px]">{{ node.verification_status }}</span>
          </div>
        </div>

        <p v-else class="text-xs rounded-lg border p-2.5" style="color: var(--text-muted); border-color: var(--border); background-color: var(--bg-primary)">
          No mapped location for this node.
        </p>

        <div class="grid grid-cols-2 gap-2 mt-2">
          <button class="btn-secondary text-xs" @click="emit('edit-location', node)">
            {{ hasLocation ? 'Edit Location' : 'Set Location' }}
          </button>
          <button class="btn-secondary text-xs" :disabled="!hasLocation" @click="emit('open-map-location', node)">
            Open Map
          </button>
        </div>
      </div>

      <!-- Evidence -->
      <div class="px-4 py-3 border-b" style="border-color: var(--border)">
        <div class="flex items-center justify-between gap-2 mb-2">
          <p class="text-xs font-semibold uppercase tracking-wider" style="color: var(--text-muted)">
            Evidence
          </p>
          <div class="flex items-center gap-1.5">
            <span class="badge text-[10px]" :class="evidenceItems.length ? 'badge-blue' : 'badge-slate'">
              {{ evidenceLoading ? '…' : evidenceItems.length }}
            </span>
            <button class="btn-secondary text-xs px-2.5 py-1.5" @click="emit('attach-evidence', node)">
              Attach Evidence
            </button>
          </div>
        </div>

        <div v-if="evidenceLoading" class="text-xs py-2" style="color: var(--text-muted)">
          Loading evidence…
        </div>

        <div v-else-if="evidenceItems.length === 0" class="space-y-2">
          <p class="text-xs" style="color: var(--text-muted)">No evidence linked to this node.</p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="item in evidenceItems"
            :key="item.id"
            class="rounded-lg p-2.5 border space-y-2"
            style="background-color: var(--bg-primary); border-color: var(--border)"
          >
            <img
              v-if="item.thumbnail_url"
              :src="item.thumbnail_url"
              :alt="item.title"
              class="w-full h-24 object-cover rounded border"
              style="border-color: var(--border); background-color: var(--bg-tertiary)"
            />
            <div class="min-w-0">
              <p class="text-xs font-medium truncate" style="color: var(--text-primary)" :title="item.title">
                {{ item.title }}
              </p>
              <div class="flex flex-wrap gap-1 mt-1">
                <span class="badge badge-blue text-[9px]">{{ item.evidence_type }}</span>
                <span v-if="item.file_size" class="badge badge-slate text-[9px]">{{ fmtBytes(item.file_size) }}</span>
              </div>
            </div>
            <p v-if="item.description" class="text-[10px] line-clamp-2" style="color: var(--text-secondary)">
              {{ item.description }}
            </p>
            <p class="text-[10px]" style="color: var(--text-muted)">Added {{ fmtDate(item.created_at) }}</p>
            <div class="flex gap-2">
              <button v-if="item.preview_url" class="btn-ghost text-[10px] px-0" @click="emit('preview-evidence', item)">
                Preview
              </button>
              <button v-if="item.download_url" class="btn-ghost text-[10px] px-0" @click="emit('download-evidence', item)">
                Download
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Connections -->
      <div class="px-4 py-3">
        <p class="text-xs font-semibold uppercase tracking-wider mb-2" style="color: var(--text-muted)">
          Connections
          <span class="ml-1 normal-case font-normal" style="color: var(--text-muted)">({{ connectedEdges.length }})</span>
        </p>

        <div v-if="connectedEdges.length === 0" class="text-xs py-3" style="color: var(--text-muted)">
          No connections.
        </div>

        <div class="space-y-2">
          <div v-for="edge in connectedEdges" :key="edge.id"
            class="rounded-lg p-2.5 border space-y-1.5"
            style="background-color: var(--bg-primary); border-color: var(--border)">
            <div class="flex items-center justify-between gap-2">
              <span class="text-[10px] font-mono" style="color: var(--text-secondary)">
                {{ (edge.relationship || edge.label || '').replace(/_/g, ' ') }}
              </span>
              <span v-if="edge.confidence != null" class="text-[10px] font-mono shrink-0" :class="confColor(edge.confidence)">
                {{ Math.round((edge.confidence ?? 0) * 100) }}%
              </span>
            </div>
            <div v-if="linkedNode(edge)" class="flex items-center gap-1.5">
              <span class="badge text-[10px] shrink-0" :class="KIND_BADGE[linkedNode(edge).kind] || 'bg-slate-500/20 text-slate-300'">
                {{ linkedNode(edge).kind.replace(/_/g, ' ') }}
              </span>
              <span class="text-[10px] font-mono truncate" style="color: var(--text-primary)" :title="linkedNode(edge).value">
                {{ linkedNode(edge).value }}
              </span>
            </div>
            <div v-if="edge.source_module" class="flex items-center gap-1 text-[9px]" style="color: var(--text-muted)">
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5"/>
              </svg>
              {{ edge.source_module }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scan from node action -->
    <div class="shrink-0 px-4 py-3 border-t" style="border-color: var(--border)">
      <button
        v-if="isManualEntity"
        class="btn-secondary w-full flex items-center justify-center gap-2 text-sm mb-2"
        @click="emit('edit-node', node)"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path d="m16.862 4.487 1.688-1.688a1.875 1.875 0 1 1 2.652 2.652L9.38 17.273 5.75 18.25l.977-3.63L16.862 4.487Z"/>
          <path d="M19.5 7.125 16.875 4.5"/>
        </svg>
        Edit node
      </button>
      <button class="btn-secondary w-full flex items-center justify-center gap-2 text-sm mb-2"
        @click="emit('add-timeline-event', node)">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path d="M12 6v6l4 2"/><circle cx="12" cy="12" r="9"/>
        </svg>
        Add timeline event
      </button>
      <button class="btn-primary w-full flex items-center justify-center gap-2 text-sm"
        @click="emit('scan-from-node', node)">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"/>
        </svg>
        Scan from this node
      </button>
    </div>
  </aside>
</template>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.18s ease-out;
}
@keyframes slideIn {
  from { transform: translateX(16px); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}
</style>
