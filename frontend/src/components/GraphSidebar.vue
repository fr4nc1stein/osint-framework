<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  graphData:  { type: Object,  default: null },
  seedValue:  { type: String,  default: '' },
  seedKind:   { type: String,  default: '' },
})

const emit = defineEmits(['node:select'])

// ── Section definitions for OSINT node kinds ─────────────────────────────
const SECTIONS = [
  { id: 'people',   title: 'People & Identity', icon: '👤', kinds: ['person', 'alias'] },
  { id: 'network',  title: 'DNS & Network',  icon: '🌐', kinds: ['domain', 'subdomain', 'hostname', 'ip', 'nameserver'] },
  { id: 'infra',    title: 'Infrastructure', icon: '🖥️', kinds: ['server', 'asn', 'isp', 'port', 'service'] },
  { id: 'contact',  title: 'Contact',        icon: '📧', kinds: ['email', 'phone', 'username'] },
  { id: 'org',      title: 'Organizations',  icon: '🏢', kinds: ['organization', 'company', 'registrar'] },
  { id: 'profiles', title: 'Profiles & URLs',icon: '🔗', kinds: ['profile_url', 'social_profile', 'url'] },
  { id: 'rep',      title: 'Reputation',     icon: '🛡️', kinds: ['reputation', 'category'] },
  { id: 'threats',  title: 'Threats',        icon: '⚠️', kinds: ['breach', 'threat', 'cve'] },
  { id: 'location', title: 'Location',       icon: '📍', kinds: ['address', 'location'] },
  { id: 'assets',   title: 'Assets',         icon: '▣', kinds: ['vehicle', 'document'] },
  { id: 'other',    title: 'Other',          icon: '•',  kinds: [] }, // catch-all
]

const KNOWN_KINDS = new Set(SECTIONS.flatMap(s => s.kinds))

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

const openSections = ref(new Set(['network', 'infra', 'threats']))
const copiedId     = ref(null)

const nodes = computed(() => props.graphData?.nodes ?? [])
const edges = computed(() => props.graphData?.edges ?? [])

// Seed node — the one whose value matches the scan target
const seedNode = computed(() =>
  nodes.value.find(n => n.value?.toLowerCase() === props.seedValue?.toLowerCase())
)

// Group nodes into sections; unknown kinds go to 'other'
const grouped = computed(() => {
  const map = new Map()
  for (const s of SECTIONS) map.set(s.id, [])

  for (const n of nodes.value) {
    if (seedNode.value && n.id === seedNode.value.id) continue // shown separately at top
    const sec = SECTIONS.find(s => s.kinds.includes(n.kind))
    if (sec) {
      map.get(sec.id).push(n)
    } else {
      map.get('other').push(n)
    }
  }
  return map
})

const visibleSections = computed(() =>
  SECTIONS.filter(s => (grouped.value.get(s.id) ?? []).length > 0)
)

function toggle(id) {
  const next = new Set(openSections.value)
  next.has(id) ? next.delete(id) : next.add(id)
  openSections.value = next
}

function avgConf(node) {
  const connected = edges.value.filter(e => e.source === node.id || e.target === node.id)
  if (!connected.length) return null
  const avg = connected.reduce((s, e) => s + (e.confidence ?? 0), 0) / connected.length
  return Math.round(avg * 100)
}

function sourceModule(node) {
  const edge = edges.value.find(e => e.target === node.id || e.source === node.id)
  return edge?.source_module ?? null
}

async function copy(node) {
  await navigator.clipboard.writeText(node.value)
  copiedId.value = node.id
  setTimeout(() => { copiedId.value = null }, 1200)
}

function truncate(val, max = 28) {
  if (!val || val.length <= max) return val
  try {
    const u = new URL(val)
    const host = u.hostname.replace('www.', '')
    const seg  = u.pathname.split('/').filter(Boolean)[0] ?? ''
    const s = seg ? `${host}/${seg}` : host
    return s.length <= max ? s : s.slice(0, max - 1) + '…'
  } catch {
    return val.slice(0, max - 1) + '…'
  }
}

const totalNodes = computed(() => nodes.value.length)
const highRisk   = computed(() => nodes.value.filter(n => n.kind === 'breach' || n.kind === 'threat' || n.kind === 'cve').length)
</script>

<template>
  <aside class="w-72 shrink-0 flex flex-col border-r overflow-hidden" style="background-color: var(--bg-sidebar); border-color: var(--border)">

    <!-- Header -->
    <div class="px-4 py-3 border-b shrink-0" style="border-color: var(--border)">
      <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Indicators</h2>
      <p class="text-xs mt-0.5" style="color: var(--text-muted)">Grouped by type · {{ totalNodes }} total</p>
    </div>

    <!-- Scrollable body -->
    <div class="flex-1 overflow-y-auto">

      <!-- ── Seed / Parent node ──────────────────────────────── -->
      <div v-if="seedNode || seedValue" class="border-b" style="border-color: var(--border)">
        <div class="px-3 py-2 text-xs font-semibold uppercase tracking-widest" style="color: var(--text-muted)">
          Seed Target
        </div>
        <div
          class="mx-3 mb-3 rounded-lg border-2 p-3 cursor-pointer transition-all hover:brightness-110"
          style="background-color: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.4)"
          @click="seedNode && emit('node:select', seedNode)"
        >
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="badge text-[10px]" :class="KIND_BADGE[seedKind] || 'bg-blue-500/20 text-blue-300'">
              {{ seedKind }}
            </span>
            <svg class="h-3 w-3 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </div>
          <p class="text-xs font-mono font-semibold break-all" style="color: var(--text-primary)">{{ seedValue }}</p>
        </div>
      </div>

      <!-- ── Collapsible sections ──────────────────────────────── -->
      <div v-for="section in visibleSections" :key="section.id" class="border-b" style="border-color: var(--border)">
        <!-- Section header -->
        <button
          class="flex w-full items-center justify-between px-3 py-2.5 text-left transition-all hover:brightness-110"
          style="background-color: var(--bg-secondary)"
          @click="toggle(section.id)"
        >
          <div class="flex items-center gap-2">
            <span class="text-sm">{{ section.icon }}</span>
            <span class="text-xs font-semibold" style="color: var(--text-primary)">{{ section.title }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs font-mono px-1.5 py-0.5 rounded" style="background-color: var(--bg-tertiary); color: var(--text-muted)">
              {{ grouped.get(section.id)?.length ?? 0 }}
            </span>
            <svg class="h-3.5 w-3.5 transition-transform" :class="openSections.has(section.id) ? 'rotate-180' : ''"
              style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </div>
        </button>

        <!-- Section items -->
        <div v-if="openSections.has(section.id)" class="p-2 space-y-1.5">
          <div
            v-for="node in grouped.get(section.id)" :key="node.id"
            class="rounded-md border p-2.5 cursor-pointer transition-all hover:border-opacity-60"
            :class="node.kind === 'breach' || node.kind === 'threat' || node.kind === 'cve'
              ? 'border-red-900/50 bg-red-950/10 hover:bg-red-950/20'
              : ''"
            :style="!(node.kind === 'breach' || node.kind === 'threat' || node.kind === 'cve')
              ? `background-color: var(--bg-primary); border-color: var(--border)`
              : ''"
            @click="emit('node:select', node)"
          >
            <div class="flex items-start justify-between gap-1.5">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5 mb-1 flex-wrap">
                  <span class="badge text-[10px]" :class="KIND_BADGE[node.kind] || 'bg-slate-500/20 text-slate-300'">
                    {{ node.kind.replace(/_/g, ' ') }}
                  </span>
                  <span v-if="avgConf(node) !== null" class="text-[10px] font-mono"
                    :class="avgConf(node) >= 85 ? 'text-emerald-400' : avgConf(node) >= 60 ? 'text-amber-400' : 'text-red-400'">
                    {{ avgConf(node) }}%
                  </span>
                </div>
                <p class="text-xs font-mono break-all leading-tight" style="color: var(--text-primary)" :title="node.value">
                  {{ truncate(node.value) }}
                </p>
                <p v-if="sourceModule(node)" class="text-[10px] mt-1 truncate font-mono" style="color: var(--text-muted)">
                  {{ sourceModule(node) }}
                </p>
              </div>
              <!-- Copy button -->
              <button class="shrink-0 p-1 rounded transition-all hover:bg-slate-700" :title="copiedId === node.id ? 'Copied' : 'Copy'"
                @click.stop="copy(node)">
                <svg v-if="copiedId !== node.id" class="h-3.5 w-3.5" style="color: var(--text-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6">
                  <path d="M8 7.5V6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-1.5M6 7.5h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z"/>
                </svg>
                <svg v-else class="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path d="m5 13 4 4L19 7"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-if="visibleSections.length === 0" class="flex flex-col items-center justify-center h-40 gap-2">
        <p class="text-xs" style="color: var(--text-muted)">No indicators yet</p>
      </div>
    </div>

    <!-- Footer summary -->
    <div class="shrink-0 border-t p-3" style="border-color: var(--border)">
      <div class="rounded-lg border p-3" style="border-color: var(--border); background-color: var(--bg-secondary)">
        <div class="grid grid-cols-3 gap-2 text-center">
          <div>
            <p class="text-sm font-bold font-mono text-blue-400">{{ totalNodes }}</p>
            <p class="text-[9px] uppercase tracking-wide" style="color: var(--text-muted)">Nodes</p>
          </div>
          <div>
            <p class="text-sm font-bold font-mono text-purple-400">{{ edges.length }}</p>
            <p class="text-[9px] uppercase tracking-wide" style="color: var(--text-muted)">Edges</p>
          </div>
          <div>
            <p class="text-sm font-bold font-mono" :class="highRisk > 0 ? 'text-red-400' : 'text-emerald-400'">
              {{ highRisk }}
            </p>
            <p class="text-[9px] uppercase tracking-wide" style="color: var(--text-muted)">Threats</p>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>
