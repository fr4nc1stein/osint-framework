# OSIF v2.0 - Phase 3.1 Plan: Enhanced UI & Case Management

**Timeline:** Week 11-12  
**Status:** 📋 Planning  
**Focus:** Case-centric investigation workflow with advanced UI features

---

## 🐛 Bug Prevention: Lessons from Phases 1–3

Before writing a single line of code, these are the hard-won fixes from previous phases. Every item here is a real bug we hit — not a hypothetical.

### SQLAlchemy Pitfalls (Phase 1)

| Rule | Why |
|------|-----|
| Never name a column `metadata` | Reserved by SQLAlchemy's Declarative API — use `meta` |
| Never name a column `relationship` | Shadows `sqlalchemy.orm.relationship()` — use `relationship_type` |
| Association tables must use `Column(...)` | `mapped_column(...)` causes `'SchemaItem' object expected` error |
| Check all new model field names against SQLAlchemy reserved words | `registry`, `metadata`, `relationship`, `info` are all reserved |

### Dependency Management (Phase 1)

| Rule | Why |
|------|-----|
| Keep `arq` pinned to `redis[hiredis]<5` | arq 0.26.x requires `redis>=4.2,<5` |
| Never put pytest/httpx-mock in main `requirements.txt` | Breaks Docker build — keep in separate `requirements-dev.txt` |
| Always verify latest available package versions before pinning | `tomba-io==1.0.0` didn't exist — it was `1.0.5` |

### Module Registration (Phase 2)

| Rule | Why |
|------|-----|
| Always use `MODULE_ID`, never `PLUGIN_ID` | Registry checks for `MODULE_ID` — wrong name = silent failure |
| After adding a module, immediately verify with `GET /api/v1/modules` | Discovery failure shows no error, just wrong count |
| Keep module naming consistent with existing pattern | `class NameModule(BaseOSINTModule)` + `MODULE_ID = "snake_case"` |

### Alembic Migration (Phases 2 & 3)

| Rule | Why |
|------|-----|
| **Import every new model in `alembic/env.py`** | Without import, autogenerate generates empty migrations silently |
| After adding a model, import it in `app/models/__init__.py` too | Keeps imports consistent and models discoverable |
| Run `docker-compose down && docker-compose up -d --build` — not just `up --build` | Cached layers can hide new files inside the container |
| Delete empty migration files before creating the real one | Empty migrations chain and create confusion |
| One migration per logical change — don't batch unrelated tables | Easier rollback and debugging |

### Docker / Port Conflicts (Phase 1)

| Ports in use | Mapping |
|-------------|---------|
| PostgreSQL | host `5434` → container `5432` |
| Redis | host `6381` → container `6379` |
| Backend API | host `6000` → container `6000` |
| Frontend | host `3000` → container `80` |

---

## 🎯 Phase 3.1 Objectives

Transform OSIF from a scan-centric tool to a **case-centric investigation platform** with:
- Case management as the primary workflow
- Correlated multi-scan investigations
- Interactive graph-based scan initiation
- AI-powered analysis and reporting
- Flexible theming (dark/light mode)
- Integration management UI

---

## 📋 Feature Breakdown

### 1. **Case Management System** (Priority: HIGH)

**What already exists (don't rebuild):**
- `Case` model in `backend/app/models/case.py` — has `status`, `priority`, `tags`, `assigned_to`, `closed_at`
- Cases API in `backend/app/api/v1/cases.py` — full CRUD
- `Scan.case_id` FK → Cases (already linked)
- `Case.scans` relationship (already defined)

**Backend additions needed:**
- Add `parent_scan_id` FK on `Scan` model (new field, requires migration)
- Add `GET /api/v1/scans/{id}/children` endpoint
- Add `GET /api/v1/cases/{id}/graph` endpoint (merges all scan graphs)
- Add `GET /api/v1/cases/{id}/scans` endpoint (scans grouped by case)
- Case status workflow endpoint: `PATCH /api/v1/cases/{id}/status`

**Migration guard:**
```python
# After adding parent_scan_id to Scan model:
# 1. Import in alembic/env.py (already imports Scan via app.models)
# 2. Run: alembic revision --autogenerate -m "add parent_scan_id to scans"
# 3. Verify migration is NOT empty before running it
# 4. alembic upgrade head
```

**Frontend additions:**
- **New Sidebar Items**: "Cases" (primary), "Reports", "AI Analyst"
- **Cases List View** (`/cases`):
  - Grid/List of all cases
  - Filter by status (open, active, closed), priority, date
  - Create new case button
  - Case cards showing: title, description, scan count, status, priority badge
  
- **Case Detail View** (`/cases/:id`):
  - Case header: title, status badge, priority, assigned_to, tags
  - Tabs:
    - **Scans** — Hierarchical list of scans in this case
    - **Graph** — Unified graph from all scans combined
    - **Timeline** — Chronological activity feed
    - **Notes** — Investigation notes (rich text)
    - **Reports** — Case-specific generated reports

---

### 2. **Hierarchical Scan Relationships** (Priority: HIGH)

**Backend changes:**

Add `parent_scan_id` to `Scan` model:
```python
# In backend/app/models/scan.py
parent_scan_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("scans.id", ondelete="SET NULL"),
    nullable=True
)

# Self-referential relationship
parent: Mapped["Scan | None"] = relationship(
    "Scan", remote_side="Scan.id", back_populates="children"
)
children: Mapped[List["Scan"]] = relationship(
    "Scan", back_populates="parent"
)
```

**Bug prevention note:** `parent_scan_id` is not a reserved SQLAlchemy name — safe to use.

**New API endpoints:**
- `GET /api/v1/scans/{id}/children` — list child scans
- `POST /api/v1/scans` — add optional `parent_scan_id` field to existing schema

**Frontend:**
- **Scan Tree View** in Case Detail Scans tab
- Visual hierarchy: parent → child indentation
- Collapse/expand branches
- "Create child scan" button on each scan row

---

### 3. **Context Menu: Scan from Graph Node** (Priority: HIGH)

**Backend:**
- New endpoint: `GET /api/v1/modules/suggest?node_type={type}`
  - Reuses existing module registry, filters by `TARGET_KINDS`
  - Returns applicable modules for a node type

**Frontend (`GraphVisualization.vue` extension):**
```javascript
// Right-click context menu on Cytoscape nodes
cy.on('cxttap', 'node', (evt) => {
  const node = evt.target.data();
  showContextMenu(node, evt.renderedPosition);
});
```

**Node-type → Module mapping:**
```
ip      → ip_geolocation, abuseipdb, shodan_lookup
domain  → dns_records, whois_lookup, subdomain_enum, virustotal_domain, urlscan_lookup
email   → hibp_breach, email_domain
```

**Context menu component** (`NodeContextMenu.vue`):
- Absolutely positioned div at mouse position
- Click outside to dismiss
- Lists suggested modules as clickable items
- Opens `CreateScanModal` pre-filled with node value + type + `parentScanId` + `caseId`

---

### 4. **Unified Case Graph** (Priority: MEDIUM)

**Backend — new endpoint:**
```python
# GET /api/v1/cases/{case_id}/graph
# 1. Fetch all scans for the case
# 2. For each scan, fetch its graph (indicators + edges)
# 3. Merge: deduplicate nodes by (value, kind)
# 4. Tag each node/edge with scan_origin list
# Returns: { nodes: [...], edges: [...], scans: [...] }
```

**Deduplication key:** `(indicator.value.lower(), indicator.kind)` — same logic as `graph_service.py`'s upsert.

**Frontend:**
- Case Detail "Graph" tab uses new `GET /api/v1/cases/:id/graph`
- Color-code nodes by source scan (each scan gets a distinct color)
- Legend showing scan label → color mapping
- Filter controls: toggle visibility per scan
- Node tooltip: "Found in: Scan 1, Scan 3"

---

### 5. **Reports System** (Priority: MEDIUM)

**New model** (`backend/app/models/report.py`):
```python
class Report(Base):
    __tablename__ = "reports"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text)          # Markdown
    report_format: Mapped[str] = mapped_column(String(20), default="markdown")  # NOT "format" — reserved in some contexts
    report_type: Mapped[str] = mapped_column(String(50), default="summary")     # NOT "type" — shadows Python builtin
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    generated_by: Mapped[str] = mapped_column(String(50), default="user")
```

**Bug prevention notes:**
- Field named `report_format` not `format` — `format` is a Python builtin
- Field named `report_type` not `type` — `type` is a Python builtin
- NOT named `metadata` or `relationship` — those crash SQLAlchemy

**Alembic checklist for Report:**
- [ ] Add `from app.models.report import Report` to `alembic/env.py`
- [ ] Add `Report` to `app/models/__init__.py`
- [ ] Run `alembic revision --autogenerate -m "add reports table"`
- [ ] Verify migration file has actual table creation, not empty `pass`
- [ ] Run `alembic upgrade head`

**API endpoints:**
- `POST /api/v1/cases/{id}/reports` — generate report
- `GET /api/v1/cases/{id}/reports` — list reports for case
- `GET /api/v1/reports` — all reports (sidebar list)
- `GET /api/v1/reports/{id}` — get report content
- `DELETE /api/v1/reports/{id}` — delete report

**Frontend:**
- Reports sidebar navigation item
- Case detail "Reports" tab
- "Generate Report" button → modal: choose type (Summary / Technical / Timeline)
- Report viewer: rendered Markdown
- Download button (Markdown / plain text export)

---

### 6. **Integrations Management UI** (Priority: LOW — Mockup)

**Backend — read-only for Phase 3.1:**

Static config in `backend/app/api/v1/integrations.py`:
```python
INTEGRATIONS_CATALOG = [
    {"id": "shodan",         "name": "Shodan",            "env_var": "SHODAN_API_KEY",        "description": "Port scanning & banner grabbing"},
    {"id": "virustotal",     "name": "VirusTotal",        "env_var": "VIRUSTOTAL_API_KEY",    "description": "File & URL reputation"},
    {"id": "abuseipdb",      "name": "AbuseIPDB",         "env_var": "ABUSEIPDB_API_KEY",     "description": "IP reputation & abuse reports"},
    {"id": "tomba",          "name": "Tomba.io",          "env_var": "TOMBA_API_KEY",         "description": "Email discovery & verification"},
    {"id": "hibp",           "name": "Have I Been Pwned", "env_var": "HIBP_API_KEY",          "description": "Data breach checking"},
    {"id": "hunter",         "name": "Hunter.io",         "env_var": "HUNTER_API_KEY",        "description": "Email finder"},
    {"id": "ipinfo",         "name": "IPinfo",            "env_var": "IPINFO_TOKEN",          "description": "IP geolocation & ASN"},
    {"id": "alienvault",     "name": "AlienVault OTX",   "env_var": "ALIENVAULT_API_KEY",    "description": "Threat intelligence feeds"},
    {"id": "censys",         "name": "Censys",            "env_var": "CENSYS_API_KEY",        "description": "Internet-wide scanning data"},
]

# GET /api/v1/integrations — returns catalog + is_configured (checks if env var is set)
```

**No database model needed in Phase 3.1** — purely reads environment variables.

**Frontend:**
- `/integrations` route
- Card grid (3 per row on desktop)
- Each card: name, description, status badge (Configured ✅ / Not Configured ❌)
- Masked API key input (UI-only for now, no save)
- "Test Connection" button (no-op placeholder in Phase 3.1)

---

### 7. **Theme Switching (Dark/Light Mode)** (Priority: MEDIUM)

**Frontend implementation:**

New Pinia store (`frontend/src/stores/theme.js`):
```javascript
export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: localStorage.getItem('osif-theme') || 'dark'
  }),
  actions: {
    init() {
      document.documentElement.setAttribute('data-theme', this.theme);
    },
    toggle() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('osif-theme', this.theme);
      document.documentElement.setAttribute('data-theme', this.theme);
    }
  }
});
```

**CSS variables in `style.css`:**
```css
:root[data-theme="dark"] {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border: #334155;
  --accent: #3b82f6;
}

:root[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #e2e8f0;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --border: #e2e8f0;
  --accent: #2563eb;
}
```

**Scope:** Replace all hardcoded Tailwind color classes in `App.vue`, `AppSidebar.vue`, `Dashboard.vue`, `ScanView.vue`, `Templates.vue` with CSS variable references.

---

### 8. **AI Settings & AI Analyst** (Priority: MEDIUM)

**Backend — no new DB table in Phase 3.1:**
- AI settings stored in environment variables / `.env` only
- `GET /api/v1/ai/settings` — returns current config (provider, model, has_key)
- `POST /api/v1/ai/analyze` — sends case/scan context to configured LLM

**No `AISettings` DB model in Phase 3.1** — avoids another migration risk. Settings live in env vars:
```
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=...
```

**Frontend (`/settings/ai`):**
- Provider dropdown: OpenAI / Anthropic / Ollama
- Model dropdown (filtered by provider)
- API key input (masked)
- Temperature slider
- "Test connection" button

**AI Analyst View (`/ai`):**
- Chat interface
- Context selector: "Current case", "Current scan", "All data"
- Suggested prompts: "Summarize findings", "Key indicators", "Suggest next steps"
- Streamed responses (SSE or polling)

---

### 9. **Additional Features & Improvements**

#### A. Investigation Timeline (Priority: HIGH)
No new table needed — derive from existing timestamps:
- Scan `created_at` → "Scan started"
- Scan `finished_at` → "Scan completed"
- Report `generated_at` → "Report generated"
- Case `created_at`, `closed_at` → Case lifecycle events

Frontend: chronological list in Case Detail "Timeline" tab.

#### B. Global Search (Priority: HIGH)
Backend: `GET /api/v1/search?q={query}&type={case|scan|indicator}`
- Simple `ILIKE %query%` across cases.title, scans.seed_value, indicators.value
- No new models — uses existing tables

#### C. Dashboard Analytics (Priority: MEDIUM)
Backend: `GET /api/v1/stats`
- Active cases count
- Scans by status (queued/running/completed/error)
- Total indicators discovered
- Recent activity (last 10 events across all cases)

No new table — derived from existing data.

#### D. Case Notes (Priority: MEDIUM)
New model (`backend/app/models/case_note.py`):
```python
class CaseNote(Base):
    __tablename__ = "case_notes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(20), default="text")   # NOT "type"
    author: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Alembic checklist for CaseNote:**
- [ ] Add `from app.models.case_note import CaseNote` to `alembic/env.py`
- [ ] Add `CaseNote` to `app/models/__init__.py`
- [ ] Single migration: `alembic revision --autogenerate -m "add case_notes table"`
- [ ] Verify migration is non-empty before running
- [ ] `alembic upgrade head`

#### E. Input Validation (Priority: HIGH)
Frontend: validate scan targets before submission:
- IP: regex `/^(\d{1,3}\.){3}\d{1,3}$/`
- Domain: regex `/^[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9](\.[a-zA-Z]{2,})+$/`
- Email: standard email regex

Backend: add Pydantic validators to scan schema:
```python
@validator('seed_value')
def validate_target(cls, v, values):
    kind = values.get('seed_kind')
    # Validate format matches kind
```

#### F. Keyboard Shortcuts (Priority: LOW)
- `Cmd/Ctrl + K` — global search
- `Cmd/Ctrl + N` — new case / new scan
- `Escape` — close modal

---

## 🗂️ Updated Information Architecture

```
OSIF v2.0 Navigation:

Sidebar:
├── 📊 Dashboard     /              (overview, stats, recent activity)
├── 📁 Cases         /cases         (PRIMARY - investigation management)
├── 🔍 Scans         /scans         (quick access to all scans)
├── 📄 Reports       /reports       (all generated reports)
├── 🔌 Integrations  /integrations  (API key status - mockup)
├── 🤖 AI Analyst    /ai            (chat with AI)
└── ⚙️ Settings      /settings/ai   (AI config, theme, preferences)

Case Detail (/cases/:id):
├── Overview    (metadata, status, actions)
├── Scans       (hierarchy tree of scans)
├── Graph       (unified multi-scan graph)
├── Timeline    (chronological activity)
├── Notes       (investigation notes)
└── Reports     (generated reports)
```

---

## 📅 Implementation Order (Bug-safe sequence)

### Step 1: Backend Models & Migration (before any API work)

1. Add `parent_scan_id` to `Scan` model
2. Create `Report` model (`report.py`)
3. Create `CaseNote` model (`case_note.py`)
4. Update `app/models/__init__.py` with all new imports
5. Update `alembic/env.py` with all new model imports
6. Run single combined migration: `alembic revision --autogenerate -m "phase3_1_schema"`
7. **Verify migration file is non-empty** before running
8. Apply: `alembic upgrade head`
9. Rebuild Docker: `docker-compose down && docker-compose up -d --build`

### Step 2: Backend API Endpoints

10. `GET /api/v1/cases/{id}/graph` — unified case graph
11. `GET /api/v1/cases/{id}/scans` — case scans list
12. `PATCH /api/v1/cases/{id}/status` — case status workflow
13. `GET /api/v1/scans/{id}/children` — child scans
14. `GET /api/v1/modules/suggest` — module suggestions by node type
15. `POST /api/v1/cases/{id}/reports` + `GET` + `DELETE` — reports CRUD
16. `POST /api/v1/cases/{id}/notes` + `GET` + `DELETE` — notes CRUD
17. `GET /api/v1/integrations` — integration catalog
18. `GET /api/v1/stats` — dashboard stats
19. `GET /api/v1/search` — global search
20. `GET /api/v1/ai/settings` + `POST /api/v1/ai/analyze` — AI endpoints
21. Register all new routers in `app/main.py`

### Step 3: Frontend Stores & Router

22. Add `theme.js` Pinia store
23. Add `cases.js` Pinia store
24. Add `reports.js` Pinia store
25. Update `api/client.js` with all new endpoints
26. Add new routes to `router/index.js`:
    - `/cases`, `/cases/:id`
    - `/reports`
    - `/integrations`
    - `/ai`
    - `/settings/ai`

### Step 4: Frontend Views (in dependency order)

27. `AppSidebar.vue` — update nav links, add theme toggle
28. `style.css` — add CSS variable theming
29. `CasesList.vue` — cases grid view
30. `CaseDetail.vue` — tabbed case detail view
31. `NodeContextMenu.vue` — right-click context menu component
32. `GraphVisualization.vue` — add context menu integration
33. `IntegrationsView.vue` — integration cards mockup
34. `ReportsView.vue` — reports list
35. `AiAnalystView.vue` — chat interface
36. `AiSettingsView.vue` — AI config form
37. `Dashboard.vue` — update with stats from `/api/v1/stats`

### Step 5: Polish & Verify

38. Test all new API endpoints via `curl` / Swagger UI
39. Verify module count still 11 after backend changes
40. Test case creation → scan → child scan → unified graph flow
41. Test theme toggle persists across page refresh
42. Run `docker-compose down && up -d --build` for final clean state

---

## 🧪 Testing Checklist

**Backend:**
- [x] `GET /api/v1/cases` returns case list
- [x] `POST /api/v1/cases` + `POST /api/v1/scans` with `case_id` links them
- [x] `GET /api/v1/cases/{id}/graph` merges graphs from multiple scans
- [x] `GET /api/v1/scans/{id}/children` returns child scans
- [x] `POST /api/v1/cases/{id}/reports` generates a report
- [x] `GET /api/v1/integrations` returns catalog with `is_configured` flag
- [x] `GET /api/v1/stats` returns aggregate counts
- [x] `GET /api/v1/search?q=example` searches across entities
- [x] Module count still 11: `curl http://localhost:6000/api/v1/modules | jq length`

**Frontend:**
- [x] Cases list loads, create case modal works
- [x] Case detail tabs all render (Scans, Graph, Timeline, Notes, Reports)
- [ ] Right-click on graph node shows context menu *(planned — Cytoscape `cxttap` hook)*
- [ ] Context menu → scan creation pre-fills target *(planned — NodeContextMenu.vue)*
- [x] Unified case graph shows all scans color-coded
- [x] Theme toggle switches dark/light and persists
- [x] Reports tab: generate → preview → download
- [x] AI Analyst chat sends message and shows response
- [x] Integrations page shows all cards with correct status
- [ ] Global search (`Cmd+K`) opens and returns results *(backend ready, frontend shortcut pending)*

---

## 📊 Success Metrics

- **User Flow**: Case creation → Scan → Discovery → Child scan → Report in < 5 min
- **Graph Performance**: Render 500+ nodes without lag (Cytoscape handles this with CoSE layout)
- **Theme Switching**: < 100ms (CSS variable swap, no re-render)
- **AI Response**: < 5s (depends on LLM provider)
- **Search**: < 500ms (indexed columns: `cases.title`, `scans.seed_value`, `indicators.value`)

---

## 🚀 Phase 3.1 Deliverables

1. ✅ Case-centric investigation workflow (Cases List + Case Detail)
2. ✅ Hierarchical scan relationships (parent/child scans)
3. ✅ Unified case graph visualization
4. ⏳ Context menu for scan-from-node *(backend `/modules/suggest` done; frontend `NodeContextMenu.vue` pending)*
5. ✅ Reports generation system
6. ✅ AI settings and analyst chat interface
7. ✅ Dark/light theme switching
8. ✅ Integrations management UI (mockup — no save)
9. ✅ Investigation timeline (derived, no new table)
10. ✅ Global search backend (`/api/v1/search`) — frontend shortcut pending

---

## 🔮 Future Phases (Phase 4+)

- **Authentication & Multi-user**: User accounts, JWT, RBAC
- **Real-time Collaboration**: Live shared cursors, shared case view
- **Advanced AI**: Auto-correlation, threat scoring, IOC enrichment
- **Production Deployment**: HTTPS, Sentry, structured logging
- **Integrations Full Backend**: Save API keys securely (vault or encrypted DB column)
- **Scan Scheduling**: Cron-based recurring scans

---

**Phase 3.1 Status:** ✅ **COMPLETE (core) — minor items pending**  
**Complexity:** High  
**Impact:** Transforms OSIF from scan tool to investigation platform

---

## ✅ Implementation Log — What Was Built & Fixed

### Date: 2026-07-01

---

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/app/models/report.py` | Report ORM model (`report_format`, `report_type` — avoids Python builtins) |
| `backend/app/models/case_note.py` | CaseNote ORM model (`note_type` — avoids `type` builtin) |
| `backend/app/api/v1/case_graph.py` | `GET /cases/{id}/graph` merged graph + `GET /cases/{id}/scans` hierarchy |
| `backend/app/api/v1/reports.py` | Report CRUD under `/cases/{id}/reports` + standalone `/reports` |
| `backend/app/api/v1/case_notes.py` | Notes CRUD under `/cases/{id}/notes` |
| `backend/app/api/v1/scan_children.py` | `GET /scans/{id}/children` |
| `backend/app/api/v1/integrations.py` | Static integration catalog, reads env vars for configured status |
| `backend/app/api/v1/stats.py` | Dashboard stats + global search endpoints |
| `backend/app/api/v1/ai.py` | AI settings read + `/ai/analyze` (Anthropic / OpenAI / Ollama) |
| `backend/app/schemas/report.py` | Report Pydantic schemas |
| `backend/app/schemas/case_note.py` | CaseNote Pydantic schemas |
| `backend/alembic/versions/b6eef2208ca7_phase3_1_schema.py` | Single combined migration: `reports`, `case_notes`, `scans.parent_scan_id` |

### Backend — Modified Files

| File | Change |
|------|--------|
| `backend/app/models/scan.py` | Added `parent_scan_id` FK + `parent`/`children` self-referential relationships |
| `backend/app/models/case.py` | Added `reports` and `notes` back-references |
| `backend/app/models/__init__.py` | Added `Report`, `CaseNote` imports |
| `backend/app/schemas/scan.py` | Added `parent_scan_id` to `ScanCreate` and `ScanResponse` |
| `backend/app/api/v1/modules.py` | Added `/suggest` endpoint **before** `/{module_id}` to prevent route shadowing |
| `backend/alembic/env.py` | Added `Report`, `CaseNote` imports for autogenerate |
| `backend/app/main.py` | Registered all 9 new routers |

### Frontend — New Files

| File | Route / Purpose |
|------|----------------|
| `frontend/src/views/ScansListView.vue` | `/scans` — all scans list with status filter + progress bar |
| `frontend/src/views/CasesList.vue` | `/cases` — case grid with create modal |
| `frontend/src/views/CaseDetail.vue` | `/cases/:id` — tabbed detail (Scans, Graph, Timeline, Notes, Reports) |
| `frontend/src/views/ReportsView.vue` | `/reports` — all reports across cases |
| `frontend/src/views/IntegrationsView.vue` | `/integrations` — integration card grid |
| `frontend/src/views/AiAnalystView.vue` | `/ai` — AI chat interface with case context selector |
| `frontend/src/views/AiSettingsView.vue` | `/settings/ai` — provider config + env instructions |
| `frontend/src/stores/theme.js` | Pinia store: dark/light toggle, localStorage persistence |
| `frontend/src/stores/cases.js` | Pinia store: cases, scans, notes, reports CRUD |

### Frontend — Modified Files

| File | Change |
|------|--------|
| `frontend/src/style.css` | Full CSS variable theming system (dark + light tokens, reusable component classes) |
| `frontend/src/App.vue` | Calls `themeStore.init()` on mount; root div uses CSS variables |
| `frontend/src/components/AppSidebar.vue` | 8 nav items, theme toggle button at bottom, CSS variable styling |
| `frontend/src/components/CreateScanModal.vue` | Accepts `defaultCaseId`, `parentScanId`, `suggestedModules` props; dark-theme styled |
| `frontend/src/components/CreateTemplateModal.vue` | Full dark-theme rewrite with CSS variables |
| `frontend/src/views/Dashboard.vue` | Rewritten: uses `/api/v1/stats`, recent cases + scans panels |
| `frontend/src/views/Templates.vue` | Full dark-theme rewrite with CSS variables |
| `frontend/src/views/ScanView.vue` | Full dark-theme rewrite; back link → `/scans`; export dropdown |
| `frontend/src/api/client.js` | Added 20+ new endpoint methods (cases, notes, reports, stats, search, AI, integrations) |
| `frontend/src/router/index.js` | Added 7 new routes: `/scans`, `/cases`, `/cases/:id`, `/reports`, `/integrations`, `/ai`, `/settings/ai` |

---

### Bugs Caught & Fixed During Implementation

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `/modules/suggest` returned module ID string instead of list | `/{module_id}` wildcard route in `modules.router` shadowed `/suggest` because `modules.router` was included first | Moved `/suggest` endpoint **into** `modules.py` above `/{module_id}`, removed duplicate from `scan_children.py` |
| Frontend build failed: "Unterminated template" | Template literal with `{{ }}` inside a Vue `{{ }}` interpolation in `AiSettingsView.vue` | Extracted to a `computed()` property (`envExample`) and referenced that in the template |
| Scans sidebar nav item showed blank page | Sidebar pointed to `/scan` (the detail route), no list view existed | Created `ScansListView.vue` at `/scans`; updated sidebar route and router |
| Templates, ScanView, CreateTemplateModal rendered white/light on dark theme | All three files used hardcoded Tailwind `bg-white`/`text-gray-*`/`border-gray-*` classes | Full rewrites using CSS variable tokens (`var(--bg-primary)`, `var(--text-primary)`, etc.) |
| `ScanView.vue` "← Back" pointed to `/` (Dashboard) | Hardcoded `$router.push('/')` | Updated to `router.push('/scans')` |

---

## 🎨 Graph Improvement Pass — Node Icons, Sidebar & Node Panel

**Date:** 2026-07-01  
**Trigger:** All graph nodes were plain circles with no visual distinction between types; graph lacked any side panel for exploring results.

---

### Problems Fixed

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| All graph nodes appeared plain blue circles | No icons, and `domain`/`subdomain`/`hostname`/`nameserver` all had near-identical dark-navy + blue colors | Embedded Lucide SVG icons as data URIs via `background-image`; assigned visually distinct bg/accent colors per kind |
| `domain`, `subdomain`, `hostname`, `nameserver` indistinguishable | KinBG was `#0c2340`/`#0a1e38` (same navy) and accents were all blue variants | Remapped: hostname→violet, nameserver→amber, subdomain→lighter blue (smaller), domain→blue (largest 50px) |
| No way to explore graph results without reading raw JSON | `ScanView` had no structured indicator list | Built `GraphSidebar.vue` with collapsible sections grouping nodes by kind |
| Clicking a node did nothing useful beyond a console.log | `GraphVisualization` only logged click events | Built `GraphNodePanel.vue` that slides in with connections, confidence bar, metadata, and "Scan from this node" |
| No way to launch a child scan from a discovered node | No UI path from graph node → scan creation | "Scan from this node" in `GraphNodePanel` opens `CreateScanModal` pre-filled with node value, kind, parent scan ID, and case ID |

---

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/components/GraphSidebar.vue` | Left panel (288px) — groups all indicators into collapsible sections by kind; seed target pinned at top; copy buttons; confidence %; source module; threat count footer |
| `frontend/src/components/GraphNodePanel.vue` | Right slide-in panel (288px) — shows on node click: kind badge, full value + copy, confidence bar, metadata, all connected edges with linked node + source module, "Scan from this node" CTA |

---

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/components/GraphVisualization.vue` | Full visual overhaul: SVG icons as data URIs per node kind (domain=globe, ip=server rack, email=envelope, breach=shield-alert, threat=warning triangle, hostname=violet, nameserver=amber, etc.); per-kind bg/accent/size; dot-grid background; zoom controls; layout switcher (cose/breadthfirst/circle/grid); legend; click-to-highlight with neighbour fade |
| `frontend/src/views/ScanView.vue` | Restructured from single-column to **3-column layout**: `GraphSidebar \| GraphVisualization \| GraphNodePanel`; stat pills in top bar; tab switcher (Graph / Events / Details) in header; node selection wires all three panels together |

---

### Node Color System (final)

| Kind | Border Accent | Size | Notes |
|------|--------------|------|-------|
| `domain` | Blue `#3b82f6` | 50px | Largest — primary target |
| `ip` | Emerald `#10b981` | 44px | Second largest |
| `breach` / `threat` | Red `#ef4444` | 44px | High-risk, large |
| `email` | Amber `#fbbf24` | 42px | |
| `organization` | Slate `#94a3b8` | 42px | |
| `subdomain` | Sky blue `#60a5fa` | 36px | Smaller than domain |
| `hostname` | Violet `#a78bfa` | 34px | Distinct from domain |
| `nameserver` | Amber `#f59e0b` | 36px | |
| `server` / `port` | Teal `#2dd4bf` | 38/30px | |
| `asn` | Indigo `#6366f1` | 36px | |
| `profile_url` / `url` | Yellow `#facc15` | 40/32px | Platform icon auto-detected (GitHub, LinkedIn, Twitter, Reddit, Instagram, YouTube, etc.) |
| `location` | Rose `#f87171` | 34px | |
| `cve` | Orange `#f97316` | 38px | |

---

### Platform Icon Detection (profile_url / url nodes)

When a node's value contains a recognisable URL, the generic link icon is replaced with the platform's icon:

`github.com` → GitHub · `linkedin.com` → LinkedIn · `twitter.com` / `x.com` → X/Twitter · `reddit.com` → Reddit · `instagram.com` → Instagram · `facebook.com` → Facebook · `t.me` / `telegram` → Telegram · `youtube.com` → YouTube · `twitch.tv` → Twitch · `discord` → Discord · `steamcommunity` / `steampowered` → Steam · *(everything else)* → Globe
