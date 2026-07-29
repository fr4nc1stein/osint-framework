# OSIF v2.0 Frontend

Vue 3 + Vite single-page application for the OSIF enterprise investigation workspace.

## Stack

- **Vue 3** with `<script setup>` Composition API
- **Vite** — fast dev server and production build
- **Pinia** — state management
- **Vue Router** — client-side routing
- **TailwindCSS** — utility-first styling with dark/light theme support
- **Cytoscape.js** — Maltego-style interactive knowledge graph
- **Leaflet / Mapbox GL** — case geolocation map
- **Chart.js** — dashboard analytics

## Development

```bash
# Requires the backend and supporting services to be running first
docker-compose -f ../docker-compose.dev.yml up -d postgres redis minio minio-init backend worker

# Install dependencies
npm install

# Start dev server (http://localhost:5173 with HMR)
npm run dev

# Type check
npm run type-check

# Lint
npm run lint

# Production build
npm run build
```

The dev server proxies `/api` and `/ws` to `http://localhost:6000` via `vite.config.ts`.

## Full Stack (Recommended)

```bash
docker-compose -f ../docker-compose.dev.yml up -d --build
```

Frontend served by Nginx at http://localhost:3000.

## Project Structure

```
src/
├── api/              # Typed axios client wrappers per resource
├── assets/           # Static assets
├── components/       # Reusable UI components
│   ├── case/         # Case workspace tab components
│   ├── graph/        # Cytoscape node/edge renderers, node panel
│   ├── scan/         # Scan modal, progress, hierarchy
│   └── ui/           # Shared: buttons, modals, badges, tables
├── composables/      # Vue composables (useGraph, useScan, useEvidence, ...)
├── router/           # Route definitions
├── stores/           # Pinia stores (case, scan, ui, auth)
├── types/            # TypeScript interfaces
└── views/            # Page-level components
    ├── DashboardView.vue
    ├── CaseListView.vue
    ├── CaseWorkspaceView.vue   # Tab host: Graph/Timeline/Evidence/Leads/Map/Dossier/Scans/Notes/Reports
    ├── ScanListView.vue
    ├── ReportListView.vue
    ├── IntegrationsView.vue
    ├── AIAnalystView.vue
    └── AISettingsView.vue
```

## Case Workspace Tabs

| Tab | Component | Description |
|---|---|---|
| Graph | `CaseGraphTab.vue` | Cytoscape.js knowledge graph with node panel |
| Timeline | `CaseTimelineTab.vue` | Chronological event log |
| Evidence | `CaseEvidenceTab.vue` | MinIO-backed file library |
| Leads | `CaseLeadsTab.vue` | Review queue — confirm/reject/promote/merge |
| Map | `CaseMapTab.vue` | Leaflet/Mapbox location markers |
| Dossier | `CaseDossierTab.vue` | Subject intelligence briefing |
| Scans | `CaseScansTab.vue` | Hierarchical scan list |
| Notes | `CaseNotesTab.vue` | Investigation notes |
| Reports | `CaseReportsTab.vue` | Generate Markdown / HTML / PDF reports |

## Environment

Copy `../.env.example` to `../.env`. The Vite dev server reads `VITE_API_BASE_URL` (defaults to `/api`).

Production builds use the Nginx config to proxy API and WebSocket traffic to the backend container — no client-side base URL configuration is needed.

## Theme

Dark/light mode toggled from the sidebar and persisted in `localStorage`. Implemented via CSS custom properties and a `dark` class on `<html>`.
