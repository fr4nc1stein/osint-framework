<script setup>
import { computed } from 'vue'
import {
  Activity,
  AlertTriangle,
  Clock3,
  Crosshair,
  Database,
  EyeOff,
  FileText,
  GitBranch,
  MapPin,
  Network,
  ShieldCheck,
  UserRound,
} from 'lucide-vue-next'

const props = defineProps({
  dossier: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  includeSensitive: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle-sensitive', 'open-graph', 'open-map', 'open-evidence', 'open-leads'])

function fmtDate(value) {
  if (!value) return 'Unknown'
  return new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function pct(value) {
  if (value == null) return 'n/a'
  return `${Math.round(value * 100)}%`
}

function primaryContact(type) {
  return (props.dossier?.entities || []).find(item => item.type === type)
}

function topTypes(counts, limit = 6) {
  return Object.entries(counts || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
}

function statusClass(value) {
  return {
    confirmed: 'text-emerald-300 border-emerald-400/40 bg-emerald-400/10',
    needs_review: 'text-amber-300 border-amber-400/40 bg-amber-400/10',
    follow_up: 'text-violet-300 border-violet-400/40 bg-violet-400/10',
    lead: 'text-sky-300 border-sky-400/40 bg-sky-400/10',
  }[value] || 'text-slate-300 border-slate-500/40 bg-slate-500/10'
}

const DOSSIER_HIDDEN_PROPERTY_KEYS = new Set([
  'address',
  'address_text',
  'lat',
  'latitude',
  'lng',
  'lon',
  'longitude',
  'location_note',
  'location_precision',
  'precision',
  'subject_profile',
])

const subjectProfileEntity = computed(() => (
  (props.dossier?.subject?.primary_entities || []).find(entity => entity.properties?.subject_profile)
  || props.dossier?.subject?.primary_entities?.[0]
  || null
))

const subjectProperties = computed(() => {
  const properties = subjectProfileEntity.value?.properties || {}
  return Object.entries(properties)
    .filter(([key]) => !DOSSIER_HIDDEN_PROPERTY_KEYS.has(key))
    .slice(0, 8)
})
</script>

<template>
  <div class="dossier-shell">
    <div v-if="loading && !dossier" class="h-72 flex items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
    </div>

    <div v-else-if="!dossier" class="dossier-empty">
      <Database class="h-10 w-10 opacity-30" />
      <p>No dossier data available.</p>
    </div>

    <div v-else class="dossier-layout">
      <section class="brief-hero">
        <div class="brief-grid"></div>
        <div class="brief-content">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2 mb-2">
                <span class="brief-chip">Dossier</span>
                <span class="brief-chip muted">{{ dossier.case.case_number }}</span>
                <span class="brief-chip" :class="dossier.case.priority === 'critical' ? 'danger' : dossier.case.priority === 'high' ? 'warn' : ''">
                  {{ dossier.case.priority }}
                </span>
              </div>
              <h2 class="brief-title">{{ dossier.subject.name }}</h2>
              <p class="brief-subtitle">{{ dossier.case.description || dossier.case.case_type || 'Consolidated case intelligence profile' }}</p>
            </div>
            <div class="brief-actions">
              <button class="btn-secondary text-xs flex items-center gap-1.5" @click="emit('open-graph')">
                <Network class="h-3.5 w-3.5" />
                Graph
              </button>
              <button class="btn-secondary text-xs flex items-center gap-1.5" @click="emit('open-map')">
                <MapPin class="h-3.5 w-3.5" />
                Map
              </button>
              <button class="btn-secondary text-xs flex items-center gap-1.5" @click="emit('toggle-sensitive')">
                <EyeOff class="h-3.5 w-3.5" />
                {{ includeSensitive ? 'Hide Sensitive' : 'Show Sensitive' }}
              </button>
            </div>
          </div>

          <div class="brief-metrics">
            <div class="metric">
              <ShieldCheck class="metric-icon text-emerald-300" />
              <span>{{ dossier.summary.confirmed_entities }}</span>
              <p>confirmed entities</p>
            </div>
            <div class="metric">
              <GitBranch class="metric-icon text-cyan-300" />
              <span>{{ dossier.summary.verified_relationships }}</span>
              <p>verified links</p>
            </div>
            <div class="metric">
              <MapPin class="metric-icon text-rose-300" />
              <span>{{ dossier.summary.locations }}</span>
              <p>locations</p>
            </div>
            <div class="metric">
              <AlertTriangle class="metric-icon text-amber-300" />
              <span>{{ dossier.summary.open_leads }}</span>
              <p>open leads</p>
            </div>
          </div>
        </div>
      </section>

      <section class="dossier-grid">
        <div class="dossier-panel subject-panel">
          <div class="panel-header">
            <UserRound class="h-4 w-4 text-cyan-300" />
            <h3>Subject Profile</h3>
          </div>
          <div class="subject-lockup">
            <div class="subject-mark">{{ (dossier.subject.name || '?').slice(0, 2).toUpperCase() }}</div>
            <div class="min-w-0">
              <p class="subject-name">{{ dossier.subject.name }}</p>
              <p class="subject-meta">{{ dossier.case.case_type || 'Investigation subject' }}</p>
            </div>
          </div>
          <div class="field-grid">
            <div>
              <span>Alias</span>
              <p>{{ (dossier.subject.aliases || []).slice(0, 3).join(', ') || 'None recorded' }}</p>
            </div>
            <div>
              <span>Email</span>
              <p>{{ primaryContact('email')?.value || 'Unknown' }}</p>
            </div>
            <div>
              <span>Phone</span>
              <p>{{ primaryContact('phone')?.value || 'Unknown' }}</p>
            </div>
            <div>
              <span>Location</span>
              <p>{{ dossier.subject.location || dossier.locations?.[0]?.label || 'Unknown' }}</p>
            </div>
          </div>
          <div v-if="subjectProperties.length" class="profile-fields">
            <div v-for="[key, value] in subjectProperties" :key="key">
              <span>{{ key.replace(/_/g, ' ') }}</span>
              <p>{{ typeof value === 'object' ? JSON.stringify(value) : value }}</p>
            </div>
          </div>
          <div class="entity-strip">
            <span v-for="entity in dossier.subject.primary_entities" :key="entity.id" class="entity-pill">
              {{ entity.type }} · {{ entity.label || entity.value }}
            </span>
          </div>
        </div>

        <div class="dossier-panel">
          <div class="panel-header">
            <Activity class="h-4 w-4 text-emerald-300" />
            <h3>Signal Composition</h3>
          </div>
          <div class="signal-list">
            <div v-for="[type, count] in topTypes(dossier.counts.entities_by_type)" :key="type" class="signal-row">
              <span>{{ type.replace(/_/g, ' ') }}</span>
              <div class="signal-bar"><i :style="`width: ${Math.min(100, count * 18)}%`"></i></div>
              <b>{{ count }}</b>
            </div>
          </div>
        </div>

        <div class="dossier-panel wide">
          <div class="panel-header">
            <Network class="h-4 w-4 text-sky-300" />
            <h3>Verified Relationship Matrix</h3>
            <button class="panel-link" @click="emit('open-graph')">Open Graph</button>
          </div>
          <div v-if="dossier.relationships.length === 0" class="panel-empty">No confirmed relationships yet.</div>
          <div v-else class="relationship-grid">
            <div v-for="rel in dossier.relationships.slice(0, 8)" :key="rel.id" class="relationship-card">
              <div class="flex items-center justify-between gap-2">
                <span class="rel-type">{{ rel.relationship }}</span>
                <span class="confidence">{{ pct(rel.confidence) }}</span>
              </div>
              <p>{{ rel.source.label || rel.source.value || rel.source.id }}</p>
              <i></i>
              <p>{{ rel.target.label || rel.target.value || rel.target.id }}</p>
            </div>
          </div>
        </div>

        <div class="dossier-panel">
          <div class="panel-header">
            <MapPin class="h-4 w-4 text-rose-300" />
            <h3>Location Board</h3>
            <button class="panel-link" @click="emit('open-map')">Open Map</button>
          </div>
          <div v-if="dossier.locations.length === 0" class="panel-empty">No confirmed locations yet.</div>
          <div v-else class="location-stack">
            <div v-for="loc in dossier.locations.slice(0, 5)" :key="loc.id" class="location-row">
              <Crosshair class="h-3.5 w-3.5 text-rose-300 shrink-0" />
              <div class="min-w-0">
                <p>{{ loc.label }}</p>
                <span>{{ Number(loc.latitude).toFixed(4) }}, {{ Number(loc.longitude).toFixed(4) }} · {{ loc.precision }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="dossier-panel">
          <div class="panel-header">
            <Clock3 class="h-4 w-4 text-amber-300" />
            <h3>Timeline Highlights</h3>
          </div>
          <div v-if="dossier.timeline.length === 0" class="panel-empty">No confirmed timeline events yet.</div>
          <div v-else class="timeline-brief">
            <div v-for="event in dossier.timeline.slice(0, 6)" :key="event.id" class="timeline-row">
              <span></span>
              <div>
                <p>{{ event.title }}</p>
                <small>{{ fmtDate(event.occurred_at) }}</small>
              </div>
            </div>
          </div>
        </div>

        <div class="dossier-panel wide">
          <div class="panel-header">
            <FileText class="h-4 w-4 text-violet-300" />
            <h3>Evidence Locker</h3>
            <button class="panel-link" @click="emit('open-evidence')">Open Evidence</button>
          </div>
          <div v-if="dossier.summary.sensitive_evidence_hidden" class="sensitive-banner">
            {{ dossier.summary.sensitive_evidence_hidden }} sensitive item{{ dossier.summary.sensitive_evidence_hidden === 1 ? '' : 's' }} hidden from this view.
          </div>
          <div v-if="dossier.evidence.length === 0" class="panel-empty">No evidence available under current filters.</div>
          <div v-else class="evidence-grid">
            <div v-for="item in dossier.evidence.slice(0, 9)" :key="item.id" class="evidence-tile">
              <div class="flex items-center justify-between gap-2">
                <span>{{ item.evidence_type }}</span>
                <EyeOff v-if="item.sensitive" class="h-3.5 w-3.5 text-amber-300" />
              </div>
              <p>{{ item.title }}</p>
              <small>{{ item.file_name || item.source_url || item.source_type }}</small>
            </div>
          </div>
        </div>

        <div class="dossier-panel">
          <div class="panel-header">
            <AlertTriangle class="h-4 w-4 text-amber-300" />
            <h3>Open Leads</h3>
            <button class="panel-link" @click="emit('open-leads')">Review</button>
          </div>
          <div v-if="dossier.leads.length === 0" class="panel-empty">No open leads.</div>
          <div v-else class="lead-stack">
            <div v-for="lead in dossier.leads.slice(0, 8)" :key="lead.id" class="lead-row">
              <span class="lead-status" :class="statusClass(lead.review_status)">{{ lead.review_status.replace(/_/g, ' ') }}</span>
              <p>{{ lead.label }}</p>
              <small>{{ lead.target_type }} · {{ lead.source_type }}</small>
            </div>
          </div>
        </div>

        <div class="dossier-panel">
          <div class="panel-header">
            <Database class="h-4 w-4 text-cyan-300" />
            <h3>Scan Provenance</h3>
          </div>
          <div v-if="dossier.scans.length === 0" class="panel-empty">No scans linked to this case.</div>
          <div v-else class="scan-stack">
            <div v-for="scan in dossier.scans.slice(0, 6)" :key="scan.id" class="scan-row">
              <div class="flex items-center justify-between gap-2">
                <p>{{ scan.seed_value }}</p>
                <span>{{ scan.status }}</span>
              </div>
              <small>{{ scan.launch_source }}{{ scan.source_node_label ? ' · ' + scan.source_node_label : '' }}</small>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dossier-shell {
  min-height: 100%;
  color: var(--text-primary);
}
.dossier-layout {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.dossier-empty {
  height: 18rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--text-muted);
}
.brief-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--border) 82%, #22d3ee);
  background:
    linear-gradient(135deg, rgba(8, 13, 24, 0.98), rgba(15, 23, 42, 0.94) 48%, rgba(26, 21, 36, 0.94)),
    repeating-linear-gradient(90deg, rgba(34, 211, 238, 0.07) 0 1px, transparent 1px 42px);
  border-radius: 8px;
}
.brief-grid {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(rgba(34, 211, 238, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(244, 114, 182, 0.05) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(90deg, black, transparent 82%);
}
.brief-content {
  position: relative;
  padding: 1rem;
}
.brief-chip {
  border: 1px solid rgba(34, 211, 238, 0.38);
  background: rgba(34, 211, 238, 0.1);
  color: #a5f3fc;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0;
}
.brief-chip.muted {
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
  color: #cbd5e1;
}
.brief-chip.warn {
  border-color: rgba(251, 191, 36, 0.45);
  background: rgba(251, 191, 36, 0.12);
  color: #fde68a;
}
.brief-chip.danger {
  border-color: rgba(248, 113, 113, 0.5);
  background: rgba(248, 113, 113, 0.12);
  color: #fecaca;
}
.brief-title {
  font-size: clamp(1.6rem, 2.6vw, 2.7rem);
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0;
  color: #f8fafc;
  max-width: 56rem;
  overflow-wrap: anywhere;
}
.brief-subtitle {
  margin-top: 0.6rem;
  color: #cbd5e1;
  max-width: 52rem;
}
.brief-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.brief-metrics {
  margin-top: 1rem;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}
.metric {
  min-height: 4.75rem;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(2, 6, 23, 0.55);
  border-radius: 6px;
  padding: 0.8rem;
}
.metric-icon {
  width: 1rem;
  height: 1rem;
}
.metric span {
  display: block;
  margin-top: 0.65rem;
  font-size: 1.45rem;
  font-weight: 800;
  color: #f8fafc;
}
.metric p {
  color: #94a3b8;
  font-size: 0.72rem;
  text-transform: uppercase;
}
.dossier-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  align-items: start;
}
.dossier-panel {
  border: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-secondary) 86%, #020617);
  border-radius: 8px;
  padding: 0.85rem;
  min-height: 14rem;
}
.dossier-panel.wide {
  grid-column: span 2;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.9rem;
}
.panel-header h3 {
  font-size: 0.8rem;
  text-transform: uppercase;
  color: var(--text-secondary);
  font-weight: 700;
  letter-spacing: 0;
}
.panel-link {
  margin-left: auto;
  color: #67e8f9;
  font-size: 0.75rem;
}
.panel-empty {
  color: var(--text-muted);
  font-size: 0.85rem;
  padding: 2rem 0;
}
.subject-lockup {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
.subject-mark {
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #ecfeff;
  font-weight: 800;
  border: 1px solid rgba(34, 211, 238, 0.4);
  background: radial-gradient(circle at 35% 30%, rgba(34, 211, 238, 0.35), rgba(15, 23, 42, 0.9));
}
.subject-name {
  font-weight: 800;
  color: #f8fafc;
  overflow-wrap: anywhere;
}
.subject-meta {
  color: var(--text-muted);
  font-size: 0.8rem;
}
.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
  margin-top: 1rem;
}
.profile-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
  margin-top: 0.8rem;
  padding-top: 0.8rem;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
}
.profile-fields span {
  color: var(--text-muted);
  font-size: 0.66rem;
  text-transform: uppercase;
}
.profile-fields p {
  color: var(--text-primary);
  font-size: 0.8rem;
  overflow-wrap: anywhere;
}
.field-grid span {
  color: var(--text-muted);
  font-size: 0.68rem;
  text-transform: uppercase;
}
.field-grid p {
  color: var(--text-primary);
  font-size: 0.82rem;
  overflow-wrap: anywhere;
}
.entity-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 1rem;
}
.entity-pill,
.lead-status {
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(148, 163, 184, 0.08);
  color: #cbd5e1;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  font-size: 0.68rem;
}
.signal-list,
.location-stack,
.lead-stack,
.scan-stack {
  display: grid;
  gap: 0.65rem;
}
.signal-row {
  display: grid;
  grid-template-columns: minmax(5rem, 1fr) 4.5rem 1.5rem;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
}
.signal-bar {
  height: 0.35rem;
  background: rgba(15, 23, 42, 0.9);
  border-radius: 999px;
  overflow: hidden;
}
.signal-bar i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #22d3ee, #a78bfa);
}
.relationship-grid,
.evidence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
}
.relationship-card,
.evidence-tile,
.location-row,
.lead-row,
.scan-row {
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(2, 6, 23, 0.35);
  border-radius: 6px;
  padding: 0.7rem;
}
.relationship-card p,
.location-row p,
.lead-row p,
.scan-row p,
.evidence-tile p {
  color: var(--text-primary);
  font-size: 0.82rem;
  overflow-wrap: anywhere;
}
.relationship-card i {
  display: block;
  height: 1px;
  margin: 0.45rem 0;
  background: linear-gradient(90deg, #22d3ee, #f472b6);
}
.rel-type,
.confidence,
.location-row span,
.lead-row small,
.scan-row small,
.scan-row span,
.evidence-tile span,
.evidence-tile small,
.timeline-row small {
  color: var(--text-muted);
  font-size: 0.7rem;
}
.location-row {
  display: flex;
  gap: 0.55rem;
}
.timeline-brief {
  position: relative;
  display: grid;
  gap: 0.65rem;
}
.timeline-row {
  display: grid;
  grid-template-columns: 0.8rem 1fr;
  gap: 0.55rem;
}
.timeline-row > span {
  width: 0.55rem;
  height: 0.55rem;
  margin-top: 0.35rem;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.12);
}
.timeline-row p {
  color: var(--text-primary);
  font-size: 0.82rem;
}
.sensitive-banner {
  border: 1px solid rgba(251, 191, 36, 0.35);
  background: rgba(251, 191, 36, 0.1);
  color: #fde68a;
  border-radius: 6px;
  padding: 0.6rem;
  font-size: 0.78rem;
  margin-bottom: 0.75rem;
}
@media (max-width: 1100px) {
  .dossier-grid,
  .brief-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .dossier-grid {
    align-items: stretch;
  }
  .dossier-panel.wide {
    grid-column: span 2;
  }
}
@media (max-width: 720px) {
  .dossier-grid,
  .brief-metrics,
  .relationship-grid,
  .evidence-grid,
  .field-grid {
    grid-template-columns: 1fr;
  }
  .dossier-panel.wide {
    grid-column: span 1;
  }
}
</style>
