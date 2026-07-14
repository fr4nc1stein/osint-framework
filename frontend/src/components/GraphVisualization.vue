<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import cytoscape from 'cytoscape'

const props = defineProps({
  graphData: { type: Object, default: null },
})

const emit = defineEmits(['node:select'])

const container = ref(null)
const activeLayout = ref('cose')
let cy = null

// ── Per-kind visual tokens ───────────────────────────────────────────────
// BG = dark tinted fill  |  ACCENT = border glow color
// Kept visually distinct: blue=domain, green=ip, amber=email,
// violet=hostname, teal=server, red=threat/breach, purple=username
const KIND_BG = {
  domain:       '#0c2340',  // navy
  person:       '#1e1b4b',  // deep indigo
  alias:        '#1f0a30',  // dark purple
  subdomain:    '#0c2340',  // navy (same family as domain)
  host:         '#1a0e38',  // dark violet (alias for hostname)
  hostname:     '#1a0e38',  // dark violet
  ip:           '#0d2b1e',  // dark green
  nameserver:   '#1f1500',  // dark amber
  server:       '#052020',  // dark teal
  asn:          '#0d1038',  // dark indigo
  isp:          '#141414',  // near-black
  port:         '#052020',  // dark teal
  service:      '#052020',  // dark teal
  email:        '#2e1a00',  // dark amber
  address:      '#200e0e',  // dark red
  phone:        '#1f0a30',  // dark purple
  username:     '#1f0a30',  // dark purple
  social_profile:'#1a1400', // dark yellow
  company:      '#141c28',  // dark slate-blue
  organization: '#141c28',  // dark slate-blue
  registrar:    '#141414',  // near-black
  profile_url:  '#1a1400',  // dark yellow
  url:          '#1a1400',  // dark yellow
  location:     '#200e0e',  // dark red
  vehicle:      '#122018',  // dark green-gray
  document:     '#141414',  // near-black
  reputation:   '#1f0e00',  // dark orange
  category:     '#052020',  // dark teal
  breach:       '#2a0808',  // dark red
  threat:       '#2a0808',  // dark red
  cve:          '#2a1200',  // dark orange-red
}

const KIND_ACCENT = {
  domain:       '#3b82f6',  // blue
  person:       '#818cf8',  // indigo
  alias:        '#c084fc',  // purple
  subdomain:    '#60a5fa',  // lighter blue
  host:         '#a78bfa',  // violet
  hostname:     '#a78bfa',  // violet
  ip:           '#10b981',  // emerald
  nameserver:   '#f59e0b',  // amber
  server:       '#2dd4bf',  // teal
  asn:          '#6366f1',  // indigo
  isp:          '#64748b',  // slate
  port:         '#22d3ee',  // cyan
  service:      '#67e8f9',  // light cyan
  email:        '#fbbf24',  // amber-yellow
  address:      '#fb7185',  // rose
  phone:        '#c084fc',  // purple
  username:     '#a78bfa',  // violet
  social_profile:'#facc15', // yellow
  company:      '#94a3b8',  // slate
  organization: '#94a3b8',  // slate
  registrar:    '#475569',  // slate-dark
  profile_url:  '#facc15',  // yellow
  url:          '#fde047',  // yellow-light
  location:     '#f87171',  // rose
  vehicle:      '#86efac',  // green
  document:     '#64748b',  // slate
  reputation:   '#fb923c',  // orange
  category:     '#34d399',  // emerald
  breach:       '#ef4444',  // red
  threat:       '#dc2626',  // red-dark
  cve:          '#f97316',  // orange
}

const KIND_SIZE = {
  domain:       50,  // largest — primary target
  person:       50,
  alias:        36,
  subdomain:    36,
  host:         34,
  hostname:     34,
  ip:           44,  // second largest — critical infra
  nameserver:   36,
  server:       38,
  asn:          36,
  isp:          34,
  port:         30,
  service:      30,
  email:        42,
  address:      38,
  phone:        36,
  username:     36,
  social_profile:40,
  company:      42,
  organization: 42,
  registrar:    34,
  profile_url:  40,
  url:          32,
  location:     34,
  vehicle:      36,
  document:     34,
  reputation:   36,
  category:     30,
  breach:       44,  // large — high risk
  threat:       44,
  cve:          38,
}

// ── SVG icon paths (Lucide, viewBox 0 0 24 24) ──────────────────────────
const KIND_ICONS = {
  domain:
    '<circle cx="12" cy="12" r="10"/>' +
    '<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>' +
    '<path d="M2 12h20"/>',
  person:
    '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  alias:
    '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/>',
  subdomain:
    '<circle cx="12" cy="12" r="10"/>' +
    '<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>' +
    '<path d="M2 12h20"/><path d="M12 2v5m0 10v5"/>',
  host:
    '<rect width="20" height="8" x="2" y="2" rx="2"/>' +
    '<rect width="20" height="8" x="2" y="14" rx="2"/>' +
    '<line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
  hostname:
    '<rect width="20" height="8" x="2" y="2" rx="2"/>' +
    '<rect width="20" height="8" x="2" y="14" rx="2"/>' +
    '<line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
  ip:
    '<rect width="20" height="8" x="2" y="2" rx="2"/>' +
    '<rect width="20" height="8" x="2" y="14" rx="2"/>' +
    '<line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>' +
    '<line x1="10" y1="6" x2="10.01" y2="6"/>',
  email:
    '<rect width="20" height="16" x="2" y="4" rx="2"/>' +
    '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
  address:
    '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  username:
    '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  phone:
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.13 12 ' +
    '19.79 19.79 0 0 1 1.06 3.37 2 2 0 0 1 3.04 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 ' +
    '2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 ' +
    '2.81.7A2 2 0 0 1 22 16.92z"/>',
  organization:
    '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/>' +
    '<path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/>' +
    '<path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/>' +
    '<path d="M10 6h4M10 10h4M10 14h4M10 18h4"/>',
  company:
    '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/>' +
    '<path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/>' +
    '<path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/>' +
    '<path d="M10 6h4M10 10h4M10 14h4M10 18h4"/>',
  registrar:
    '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>' +
    '<polyline points="14 2 14 8 20 8"/><path d="M8 13h8M8 17h5"/>',
  nameserver:
    '<path d="M4 5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5z"/>' +
    '<path d="M4 13a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-2z"/>' +
    '<path d="M7 8v5m10-5v5M7 14v3m10-3v3"/>',
  server:
    '<rect width="20" height="8" x="2" y="2" rx="2" ry="2"/>' +
    '<rect width="20" height="8" x="2" y="14" rx="2" ry="2"/>' +
    '<line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
  asn:
    '<rect x="2" y="2" width="8" height="8" rx="1"/><rect x="14" y="2" width="8" height="8" rx="1"/>' +
    '<rect x="8" y="14" width="8" height="8" rx="1"/>' +
    '<path d="M6 10v4M18 10v4M6 14h12"/>',
  isp:
    '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>' +
    '<polyline points="9 22 9 12 15 12 15 22"/>',
  location:
    '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  social_profile:
    '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>' +
    '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  vehicle:
    '<path d="M19 17h2l-1.5-4.5A3 3 0 0 0 16.65 10h-9.3a3 3 0 0 0-2.85 2.5L3 17h2"/>' +
    '<circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><path d="M5 14h14"/>',
  document:
    '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>' +
    '<polyline points="14 2 14 8 20 8"/><path d="M8 13h8M8 17h5"/>',
  reputation:
    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  category:
    '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>' +
    '<line x1="7" y1="7" x2="7.01" y2="7"/>',
  breach:
    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' +
    '<path d="M12 8v4"/><path d="M12 16h.01"/>',
  threat:
    '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>' +
    '<path d="M12 9v4"/><path d="M12 17h.01"/>',
  cve:
    '<path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 16a1 1 0 1 1 1-1 1 1 0 0 1-1 1zm1-4h-2V7h2z"/>',
  port:
    '<path d="M12 22V12"/><path d="M5 17H2a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1h-3"/>' +
    '<polygon points="12 17 7 22 17 22 12 17"/>',
  service:
    '<circle cx="12" cy="12" r="3"/>' +
    '<path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4' +
    'M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>',
  url:
    '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>' +
    '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  // Fallback
  unknown:
    '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>' +
    '<line x1="12" y1="17" x2="12.01" y2="17"/>',
}

// Platform-specific icons for profile_url / social nodes
const PLATFORM_ICONS = {
  github:
    '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 ' +
    '0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 ' +
    '3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/>' +
    '<path d="M9 18c-4.51 2-5-2-7-2"/>',
  linkedin:
    '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>' +
    '<rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
  twitter:
    '<path d="M4 4l11.733 16H20L8.267 4z"/>' +
    '<path d="M4 20l6.768-6.768M20 4l-6.768 6.768"/>',
  reddit:
    '<circle cx="12" cy="12" r="10"/><circle cx="9" cy="13.5" r="1"/><circle cx="15" cy="13.5" r="1"/>' +
    '<path d="M9 16s1 1.5 3 1.5 3-1.5 3-1.5"/>' +
    '<path d="M17 12a2 2 0 1 0-1.5 1.94M13 10.35a9.9 9.9 0 0 0-2 0"/>' +
    '<path d="M15 9.5 17 8l-.5-2.5 2.5.5"/>',
  instagram:
    '<rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>' +
    '<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>' +
    '<line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>',
  facebook:
    '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
  telegram:
    '<path d="m22 3-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 3"/>' +
    '<path d="M2 3h20v18a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2Z"/>',
  youtube:
    '<path d="M22.54 6.42a2.78 2.78 0 0 0-1.95-1.96C18.88 4 12 4 12 4s-6.88 0-8.59.46a2.78 2.78 0 0 0-1.95 1.96A29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58A2.78 2.78 0 0 0 3.41 19.6C5.12 20 12 20 12 20s6.88 0 8.59-.46a2.78 2.78 0 0 0 1.95-1.95A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58z"/>' +
    '<polygon points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02"/>',
  twitch:
    '<path d="M21 2H3v16h5v4l4-4h5l4-4V2z"/><path d="M11 7v5m5-5v5"/>',
  discord:
    '<circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/>' +
    '<path d="M7.5 7.5C9 6.5 15 6.5 16.5 7.5"/><path d="M7.5 16.5C9 17.5 15 17.5 16.5 16.5"/>' +
    '<path d="M8.5 4.5l-1 3m9-3l1 3M4 19.5l1.5-3m13 3l-1.5-3"/>',
  steam:
    '<circle cx="12" cy="12" r="10"/><path d="M12 8a4 4 0 0 1 0 8"/>' +
    '<path d="M8 12H4"/><path d="M18 12h-2"/>',
  globe:
    '<circle cx="12" cy="12" r="10"/>' +
    '<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>' +
    '<path d="M2 12h20"/>',
}

function detectPlatform(value) {
  const v = value.toLowerCase()
  if (v.includes('github.com'))    return 'github'
  if (v.includes('linkedin.com'))  return 'linkedin'
  if (v.includes('twitter.com') || v.includes('x.com')) return 'twitter'
  if (v.includes('reddit.com'))    return 'reddit'
  if (v.includes('instagram.com')) return 'instagram'
  if (v.includes('facebook.com'))  return 'facebook'
  if (v.includes('t.me') || v.includes('telegram')) return 'telegram'
  if (v.includes('youtube.com'))   return 'youtube'
  if (v.includes('twitch.tv'))     return 'twitch'
  if (v.includes('discord'))       return 'discord'
  if (v.includes('store.steampowered') || v.includes('steamcommunity')) return 'steam'
  return 'globe'
}

function buildSvgUri(svgPath, strokeColor) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="${strokeColor}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${svgPath}</svg>`
  return `url('data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}')`
}

function getNodeIcon(kind, value) {
  if (kind === 'profile_url' || kind === 'url') {
    const platform = detectPlatform(value || '')
    return buildSvgUri(PLATFORM_ICONS[platform] ?? PLATFORM_ICONS.globe, '#ffffff')
  }
  return buildSvgUri(KIND_ICONS[kind] ?? KIND_ICONS.unknown, '#ffffff')
}

function truncateLabel(value, max = 22) {
  if (!value || value.length <= max) return value
  try {
    const u = new URL(value)
    const host = u.hostname.replace('www.', '')
    const seg = u.pathname.split('/').filter(Boolean)[0] ?? ''
    const short = seg ? `${host}/${seg}` : host
    return short.length <= max ? short : short.slice(0, max - 1) + '…'
  } catch {
    return value.slice(0, max - 1) + '…'
  }
}

// ── Stats ────────────────────────────────────────────────────────────────
const uniqueNodeTypes = computed(() => {
  if (!props.graphData) return 0
  return new Set(props.graphData.nodes.map(n => n.kind)).size
})
const uniqueRelationships = computed(() => {
  if (!props.graphData) return 0
  return new Set(props.graphData.edges.map(e => e.relationship)).size
})

// ── Legend — top 6 kinds present in the graph ───────────────────────────
const legendKinds = computed(() => {
  if (!props.graphData) return []
  const counts = {}
  for (const n of props.graphData.nodes) counts[n.kind] = (counts[n.kind] || 0) + 1
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 7)
    .map(([kind, count]) => ({ kind, count }))
})

// ── Build Cytoscape elements ─────────────────────────────────────────────
function buildElements() {
  if (!props.graphData) return []
  return [
    ...props.graphData.nodes.map(n => ({
      data: { id: n.id, label: truncateLabel(n.value), kind: n.kind, value: n.value, raw: n },
    })),
    ...props.graphData.edges.map(e => ({
      data: {
        id: e.id, source: e.source, target: e.target,
        label: (e.relationship || '').replace(/_/g, ' '),
        confidence: e.confidence,
      },
    })),
  ]
}

// ── Init / destroy ───────────────────────────────────────────────────────
function initGraph() {
  if (!container.value || !props.graphData?.nodes?.length) return
  if (cy) { cy.destroy(); cy = null }

  cy = cytoscape({
    container: container.value,
    elements: buildElements(),
    wheelSensitivity: 0.25,
    minZoom: 0.05,
    maxZoom: 6,
    style: [
      {
        selector: 'node',
        style: {
          'background-color':   ele => KIND_BG[ele.data('kind')]  ?? '#1e293b',
          'background-image':   ele => getNodeIcon(ele.data('kind'), ele.data('value')),
          'background-fit':     'contain',
          'background-repeat':  'no-repeat',
          'background-width':   '48%',
          'background-height':  '48%',
          shape:                'ellipse',
          width:                ele => KIND_SIZE[ele.data('kind')] ?? 38,
          height:               ele => KIND_SIZE[ele.data('kind')] ?? 38,
          'border-color':       ele => KIND_ACCENT[ele.data('kind')] ?? '#64748b',
          'border-width':       2,
          label:                'data(label)',
          color:                '#cbd5e1',
          'font-size':          '9px',
          'text-valign':        'bottom',
          'text-margin-y':      6,
          'text-background-color':   '#020617',
          'text-background-opacity': 0.8,
          'text-background-padding': '2px',
        },
      },
      {
        selector: 'node[kind="domain"]',
        style: { 'border-width': 3, 'font-size': '10px', color: '#e2e8f0' },
      },
      {
        selector: 'node[kind="breach"], node[kind="threat"]',
        style: { 'border-width': 3 },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color':         ele => {
            const r = ele.data('label')
            if (r?.includes('BREACH') || r?.includes('THREAT')) return '#7f1d1d'
            if (r?.includes('CORROBORATED')) return '#78350f'
            return '#1d4ed8'
          },
          'target-arrow-color': '#94a3b8',
          'target-arrow-shape': 'triangle',
          'curve-style':        'bezier',
          opacity:              0.65,
          label:                'data(label)',
          'font-size':          '7px',
          color:                '#94a3b8',
          'text-rotation':      'autorotate',
          'text-margin-y':      -8,
          'text-background-color':   '#020617',
          'text-background-opacity': 0.75,
          'text-background-padding': '2px',
        },
      },
      {
        selector: 'node:selected',
        style: { 'border-color': '#38bdf8', 'border-width': 4 },
      },
      {
        selector: 'edge:selected',
        style: { 'line-color': '#38bdf8', 'target-arrow-color': '#38bdf8', opacity: 1 },
      },
      { selector: '.faded',       style: { opacity: 0.08 } },
      { selector: '.highlighted', style: { opacity: 1 } },
    ],
    layout: {
      name: activeLayout.value,
      animate: true,
      animationDuration: 400,
      nodeRepulsion: 10000,
      idealEdgeLength: 120,
      padding: 40,
    },
  })

  cy.on('tap', 'node', evt => {
    const node = evt.target
    cy.elements().removeClass('faded highlighted')
    cy.elements().addClass('faded')
    node.removeClass('faded').addClass('highlighted')
    node.connectedEdges().removeClass('faded').addClass('highlighted')
    node.neighbourhood('node').removeClass('faded').addClass('highlighted')
    emit('node:select', node.data('raw'))
  })

  cy.on('tap', evt => {
    if (evt.target === cy) cy.elements().removeClass('faded highlighted')
  })
}

function runLayout(name) {
  activeLayout.value = name
  cy?.layout({ name, animate: true, randomize: false, padding: 40 }).run()
}

function zoomIn()  { cy?.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }) }
function zoomOut() { cy?.zoom({ level: cy.zoom() / 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }) }
function fitGraph(){ cy?.fit(undefined, 40) }

watch(() => props.graphData, () => {
  if (cy) { cy.destroy(); cy = null }
  initGraph()
}, { deep: true })

onMounted(initGraph)
onUnmounted(() => { cy?.destroy(); cy = null })

defineExpose({ runLayout, zoomIn, zoomOut, fitGraph })
</script>

<template>
  <div class="relative w-full h-full overflow-hidden graph-bg">

    <!-- Empty state -->
    <div v-if="!graphData || graphData.nodes.length === 0"
      class="absolute inset-0 flex flex-col items-center justify-center gap-3" style="color: var(--text-muted)">
      <svg class="h-14 w-14 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="0.8">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
        <path d="M2 12h20"/>
      </svg>
      <p class="text-sm">No graph data yet — run a scan first</p>
    </div>

    <!-- Graph container -->
    <div ref="container" class="w-full h-full" />

    <!-- Top-right: layout controls + stats -->
    <div v-if="graphData?.nodes?.length" class="absolute top-3 right-3 z-10 flex flex-col items-end gap-2">
      <!-- Stats chip -->
      <div class="flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-mono backdrop-blur-sm"
        style="background-color: rgba(2,6,23,0.85); border-color: var(--border)">
        <span class="text-blue-400 font-medium">{{ graphData.nodes.length }}</span>
        <span style="color: var(--text-muted)">nodes</span>
        <span class="mx-1" style="color: var(--border)">·</span>
        <span class="text-purple-400 font-medium">{{ graphData.edges.length }}</span>
        <span style="color: var(--text-muted)">edges</span>
        <span class="mx-1" style="color: var(--border)">·</span>
        <span class="text-emerald-400 font-medium">{{ uniqueNodeTypes }}</span>
        <span style="color: var(--text-muted)">types</span>
      </div>

      <!-- Layout switcher -->
      <div class="flex items-center gap-0.5 rounded-md border overflow-hidden backdrop-blur-sm"
        style="background-color: rgba(2,6,23,0.85); border-color: var(--border)">
        <button v-for="l in ['cose','breadthfirst','circle','grid']" :key="l"
          class="px-2.5 py-1.5 text-xs transition-colors"
          :style="activeLayout === l
            ? 'background-color: rgba(59,130,246,0.25); color: #93c5fd; font-weight: 600'
            : 'color: var(--text-muted)'"
          @click="runLayout(l)">
          {{ l }}
        </button>
      </div>
    </div>

    <!-- Bottom-right: zoom controls -->
    <div v-if="graphData?.nodes?.length"
      class="absolute bottom-3 right-3 z-10 flex flex-col rounded-md border overflow-hidden backdrop-blur-sm"
      style="background-color: rgba(2,6,23,0.85); border-color: var(--border)">
      <button class="p-2.5 transition-colors hover:bg-slate-800" style="color: var(--text-secondary)" title="Zoom in" @click="zoomIn">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
      </button>
      <button class="p-2.5 border-t transition-colors hover:bg-slate-800" style="color: var(--text-secondary); border-color: var(--border)" title="Zoom out" @click="zoomOut">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg>
      </button>
      <button class="p-2.5 border-t transition-colors hover:bg-slate-800" style="color: var(--text-secondary); border-color: var(--border)" title="Fit to screen" @click="fitGraph">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15"/>
        </svg>
      </button>
    </div>

    <!-- Bottom-left: legend -->
    <div v-if="legendKinds.length"
      class="absolute bottom-3 left-3 z-10 rounded-md border px-3 py-2.5 backdrop-blur-sm"
      style="background-color: rgba(2,6,23,0.85); border-color: var(--border)">
      <p class="text-[9px] font-semibold uppercase tracking-widest mb-2" style="color: var(--text-muted)">Node Types</p>
      <div class="space-y-1.5">
        <div v-for="{ kind, count } in legendKinds" :key="kind" class="flex items-center gap-2">
          <span class="h-2.5 w-2.5 shrink-0 rounded-full border"
            :style="`background-color: ${KIND_BG[kind] ?? '#1e293b'}; border-color: ${KIND_ACCENT[kind] ?? '#64748b'}`"/>
          <span class="text-[9px] font-mono" style="color: var(--text-secondary)">{{ kind.replace(/_/g, ' ') }}</span>
          <span class="text-[9px] font-mono ml-auto" style="color: var(--text-muted)">{{ count }}</span>
        </div>
      </div>
    </div>

    <!-- Top-left: stat cards (in ScanView the parent container provides these, so only show here when used standalone) -->
  </div>
</template>

<style scoped>
.graph-bg {
  background-color: #020617;
  background-image:
    radial-gradient(circle, rgba(59,130,246,0.12) 1px, transparent 1px);
  background-size: 22px 22px;
}
</style>
