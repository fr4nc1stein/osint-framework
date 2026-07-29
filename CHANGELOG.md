# Changelog

All notable changes to OSIF (Open Source Intelligence Framework) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-07-16

### Major Release — Enterprise OSINT Web Workspace

Complete rewrite of OSIF as a full-stack, API-first enterprise investigation platform. The Metasploit-style CLI is retained alongside the new workspace.

---

### Added

#### Core Platform (Phase 1–2)
- FastAPI async backend with Alembic migrations run automatically on startup
- PostgreSQL + SQLAlchemy 2.0 with JSONB for flexible metadata
- arq + Redis async task queue for parallel OSINT module execution
- WebSocket real-time scan progress (`/ws/scan/{scan_id}`)
- Vue 3 frontend (Vite + Pinia + Vue Router + TailwindCSS)
- Cytoscape.js Maltego-style interactive graph visualization
- Docker Compose stack: postgres, redis, minio, minio-init, backend, worker, frontend, console
- Production `docker-compose.yaml` with resource limits, Redis auth, healthcheck-gated startup, log rotation

#### OSINT Engine (Phase 3)
- Auto-linker service — detects multi-module corroborations and infers transitive relationships
- Redis result caching per module with configurable TTL
- Per-API rate limiting backed by Redis (token bucket)
- Scan templates — reusable module presets
- Export formats: JSON, CSV, GraphML

#### Case & Investigation Workspace (Phase 3.1)
- Case management — create, edit, status/severity/assignment workflow
- Case knowledge graph — unified view merging all scan indicators
- Hierarchical scan relationships (parent → child scans)
- Case-scoped reports — markdown, text, HTML, and PDF (ReportLab)
- Report snapshots — frozen at generation time
- Investigation notes (CRUD)
- Dark/light theme with CSS variable design system
- Integration marketplace UI
- AI Analyst chat interface (Anthropic, OpenAI, Ollama)
- Dashboard analytics and global search

#### Encrypted Credentials (Phase 3.2)
- Encrypted integration credentials stored in PostgreSQL (Fernet via `APP_ENCRYPTION_KEY`)
- DB-first credential lookup with `.env` fallback for migration compatibility
- Integration test/save/delete API — secrets never returned after save
- Configurable AI settings (provider, model, base URL, temperature) stored encrypted in DB
- First-run setup banner with environment import
- HTML + PDF report renderer via ReportLab

#### PI / Skip Tracing Workspace (Phase 3.4)
- **Manual entities** — create persons, aliases, phones, addresses, social profiles, companies, vehicles, documents directly on the case graph
- **Manual relationships** — connect any two graph nodes (manual ↔ manual, manual ↔ scan indicator)
- **Case knowledge graph merge** — scan indicators + manual entities + manual relationships in one unified graph with `graph_node_type` discriminator
- **Evidence attachments** — upload files to MinIO, link URL/note/screenshot evidence to any node, edge, timeline event, report, or scan; SHA-256 hashing; image thumbnail generation
- **Timeline** — case event log with manual creation and creation from node/evidence/scan; distinct icons per event type
- **Map view** — Leaflet/Mapbox markers for location entities, address observations, IP geolocation results, and timeline sightings; marker filtering; graph/evidence/timeline jump links
- **Geolocation editing** — set/edit location from node panel or map; drag manual markers with explicit save; normalized `case_geolocations` table for multi-observation triangulation; Mapbox geocoding abstraction with external-submission consent gate
- **Leads review workflow** — scan-derived indicators and edges default to `needs_review`; promote, merge, confirm, reject, follow-up, or stale actions; bulk operations; rejected leads hidden from default graph and map
- **Scan from node** — launch enrichment scans directly from any manual or promoted node; entity-type → module mapping with kind normalization; scan results written back as reviewable leads with provenance fields
- **Dossier tab** — intelligence-briefing layout: subject hero, confirmed entities, verified relationships, location board, timeline highlights, evidence locker, open leads, scan provenance; sensitive evidence gated behind `include_sensitive=true`
- **PI reports** — dossier report type added to Markdown, HTML, and PDF renderers; includes subject profile, verified relationships, locations, timeline, evidence index, open leads, scan provenance

#### New Database Tables
- `scan_templates`
- `integration_credentials`
- `ai_settings`
- `case_entities`
- `case_relationships`
- `case_evidence`
- `case_evidence_links`
- `case_timeline_events`
- `case_timeline_links`
- `case_geolocations`
- `case_lead_reviews`

#### New API Endpoints (selected)
```
GET/POST   /api/v1/cases/{id}/entities
PUT/DELETE /api/v1/cases/{id}/entities/{eid}
GET/POST   /api/v1/cases/{id}/relationships
PUT/DELETE /api/v1/cases/{id}/relationships/{rid}
GET/POST   /api/v1/cases/{id}/evidence
POST       /api/v1/cases/{id}/evidence/upload
GET        /api/v1/cases/{id}/evidence/{eid}/download
GET        /api/v1/cases/{id}/evidence/{eid}/thumbnail
GET/POST   /api/v1/cases/{id}/timeline
GET        /api/v1/cases/{id}/map
GET        /api/v1/cases/{id}/leads
PATCH      /api/v1/cases/{id}/leads/{type}/{id}
GET        /api/v1/cases/{id}/dossier
GET        /api/v1/cases/{id}/graph
GET/PUT    /api/v1/integrations/{provider}
POST       /api/v1/integrations/{provider}/test
GET/PUT    /api/v1/ai/settings
POST       /api/v1/ai/test
```

---

### OSINT Modules (11)

| Module | Category | API Key |
|---|---|---|
| `dns_records` | domain | — |
| `subdomain_enum` | domain | — |
| `whois_lookup` | domain | — |
| `urlscan_lookup` | domain | — |
| `email_hunter` | domain | Tomba |
| `virustotal_domain` | domain | VirusTotal |
| `ip_geolocation` | ip | — |
| `abuseipdb` | ip | AbuseIPDB |
| `shodan_lookup` | ip | Shodan |
| `email_domain` | email | — |
| `hibp_breach` | email | — |

---

### Statistics
- **Branch**: `feature/v2`
- **Docker services**: 8
- **Database tables**: 21+
- **API endpoints**: 60+
- **OSINT modules**: 11
- **Frontend views**: 10+
- **Case workspace tabs**: Graph, Timeline, Evidence, Leads, Map, Dossier, Scans, Notes, Reports

---

## [1.5.0] - 2026-05-13

### Web Graph Visualization — v1 Addition

Added interactive web interface to the original CLI tool.

### Added
- Interactive graph interface (Flask + vis.js)
- AbuseIPDB IP reputation integration
- Subdomain discovery via Certificate Transparency (crt.sh)
- Smart port conflict detection (5001–5005)
- AbuseIPDB CLI module (`modules/ioc/abuseipdb.py`)
- Web server (`web_server.py`) — Flask REST API with CORS
- Quick start script (`start_web.sh`)
- Developer documentation (`.agent/` — 1,819 lines)
- Contributing guide (`CONTRIBUTING.md`)

---

## [1.1.1] - Previous Release

### Changed
- Various bug fixes and module improvements

---

## [1.1.0] - Previous Release

### Added
- Initial module system
- Basic CLI interface
- Core OSINT capabilities

---

## [1.0.0] - Initial Release

### Added
- Metasploit-style CLI interface
- Basic OSINT modules
- API integrations (VirusTotal, Shodan, etc.)

---

[2.0.0]: https://github.com/fr4nc1stein/osint-framework/compare/v1.5.0...v2.0.0
[1.5.0]: https://github.com/fr4nc1stein/osint-framework/compare/v1.1.1...v1.5.0
[1.1.1]: https://github.com/fr4nc1stein/osint-framework/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/fr4nc1stein/osint-framework/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/fr4nc1stein/osint-framework/releases/tag/v1.0.0
