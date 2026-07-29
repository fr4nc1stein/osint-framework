# OSIF v2.0.0 — Enterprise OSINT Web Workspace

**Release date:** 2026-07-16  
**Branch:** `feature/v2`

---

## Overview

OSIF v2.0.0 is a full platform rewrite. The Metasploit-style CLI is retained. Everything else is new.

The new platform is an API-first, async, containerised investigation workspace built on:
- **FastAPI** async backend (Python 3.12, SQLAlchemy 2.0, Pydantic v2)
- **arq + Redis** async task queue for parallel OSINT module execution
- **PostgreSQL** with JSONB for flexible indicator metadata
- **MinIO** S3-compatible object store for evidence files
- **Vue 3 + Cytoscape.js** investigation workspace frontend
- **Docker Compose** — 8-service stack, production-hardened

---

## What's Included

### Core Platform

- FastAPI app with Alembic auto-migrate on startup
- WebSocket real-time scan progress (`/ws/scan/{scan_id}`)
- arq worker pool for non-blocking OSINT execution
- Redis result caching (per-module TTL) and rate limiting (token bucket)
- Scan templates — reusable module presets
- Export: JSON, CSV, GraphML
- Production `docker-compose.yaml`:
  - Resource limits per service
  - Redis `--requirepass` auth
  - MinIO bucket provisioned by `minio-init`
  - Healthcheck-gated startup ordering
  - Log rotation (json-file driver)
  - No source volume mounts

### OSINT Modules (11)

| Module | Input | External API |
|---|---|---|
| `dns_records` | domain | — |
| `subdomain_enum` | domain | — |
| `whois_lookup` | domain | — |
| `urlscan_lookup` | domain | URLScan |
| `email_hunter` | domain | Tomba |
| `virustotal_domain` | domain | VirusTotal |
| `ip_geolocation` | ip | — |
| `abuseipdb` | ip | AbuseIPDB |
| `shodan_lookup` | ip | Shodan |
| `email_domain` | email | — |
| `hibp_breach` | email | HIBP |

### Case & Investigation Workspace (Phase 3.1)

- Case management with status, severity, priority, assignment, client, jurisdiction, tags
- Case knowledge graph — Cytoscape.js unified view of all scan indicators
- Hierarchical scan relationships (parent → child)
- Case-scoped reports: Markdown, Text, HTML, PDF
- Report snapshots — frozen at generation time
- Investigation notes
- Dark/light theme
- Integration marketplace UI with provider health cards
- AI Analyst chat (Anthropic, OpenAI, Ollama)
- Dashboard analytics and global search

### Encrypted Credentials (Phase 3.2)

- Fernet-encrypted integration credentials in PostgreSQL
- DB-first lookup with `.env` fallback for migration compatibility
- Secrets never returned after save
- AI settings (provider, model, base URL, temperature) stored encrypted
- HTML + PDF report renderer via ReportLab

### PI / Skip Tracing Workspace (Phase 3.4)

All 8 sub-plans complete:

**A — Manual entities**
- Create persons, aliases, phones, addresses, social profiles, companies, vehicles, documents on the case graph
- Properties stored as JSONB; entity type drives UI icon, color, and module compatibility

**B — Evidence / MinIO**
- Upload files to MinIO (`osif-evidence` bucket); SHA-256 hash; image thumbnail generation
- Link URL/note/screenshot evidence to any node, edge, timeline event, report, or scan
- Evidence preview, download, and thumbnail proxied through backend API (never direct MinIO URLs)

**C — Timeline**
- Case event log with 16 event types
- Create events manually or from graph node, evidence item, or scan
- Events with location entity appear on the Map tab

**D — Map view**
- Leaflet/Mapbox markers for location entities, address observations, IP geolocation results, sightings
- Marker panel with jump links to Graph, Evidence, and Timeline tabs
- Create new location nodes directly from the map

**E — Geolocation editing**
- Set/edit location from node panel or map
- Drag manual entity markers with explicit save step
- Normalized `case_geolocations` table for multi-observation triangulation
- Mapbox geocoding abstraction with external-submission consent gate

**F — Leads review workflow**
- Scan-derived indicators and edges default to `needs_review`
- Actions: promote, merge, confirm, reject, follow-up, stale
- Bulk operations with confirmation on bulk reject
- Rejected leads hidden from default graph and map (auditable with `include_rejected=true`)

**G — Scan from node**
- Launch enrichment scans from any manual or promoted node in the graph
- Entity-type → OSINT module mapping with kind normalization
- Scan results written back as reviewable leads with provenance fields:
  `launch_source`, `source_node_type`, `source_node_id`, `source_node_label`

**H — Dossier tab + PI reports**
- Intelligence-briefing layout: subject hero, confirmed entities, verified relationships, location board, timeline highlights, evidence locker, open leads, scan provenance
- Subject tagging: `properties.subject_profile = true` on a manual entity
- Sensitive evidence gated behind `include_sensitive=true`
- Dossier report type added to Markdown, HTML, and PDF renderers

---

## New Database Tables

```
scan_templates
integration_credentials
ai_settings
case_entities
case_relationships
case_evidence
case_evidence_links
case_timeline_events
case_timeline_links
case_geolocations
case_lead_reviews
```

Total tables: 21+

---

## New API Endpoints (selected)

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

Total endpoints: 60+

---

## Port Mapping

| Service | Host port |
|---|---|
| Frontend | 3000 |
| Backend API | 6000 |
| PostgreSQL | 5434 |
| Redis | 6381 |
| MinIO API | 9100 |
| MinIO Console | 9101 |

---

## Statistics

- Docker services: 8
- Database tables: 21+
- API endpoints: 60+
- OSINT modules: 11
- Frontend views: 10+
- Case workspace tabs: 9 (Graph, Timeline, Evidence, Leads, Map, Dossier, Scans, Notes, Reports)

---

## Breaking Changes from v1.5.0

The Flask + vis.js web interface (`web_server.py`, port 5001) is removed. The CLI itself is unchanged.

Migration path: there is no data migration from v1.5.0. Start fresh with `docker-compose up -d --build`.

---

## Known Limitations

- No user authentication or multi-tenant access control in this release (single-team deployment assumed)
- AI Analyst requires a separately provisioned LLM API key
- Mapbox geocoding requires a Mapbox token; the map renders in fallback mode without one
- PDF report generation depends on `reportlab` in the backend image

---

## Full Changelog

See [CHANGELOG.md](../CHANGELOG.md).
