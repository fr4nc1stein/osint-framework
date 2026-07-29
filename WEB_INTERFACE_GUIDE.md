# OSIF v2.0 — Web Interface Guide

## Overview

OSIF v2.0 ships a full enterprise investigation workspace accessible at **http://localhost:3000**.

The interface is built on Vue 3 with Cytoscape.js graph visualization, a MinIO-backed evidence library, and a real-time scan engine powered by WebSocket events.

---

## Getting Started

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

Open http://localhost:3000 in your browser.

---

## Navigation

The sidebar provides access to:

| Item | Route | Purpose |
|---|---|---|
| Dashboard | `/` | Stats overview, recent cases and scans |
| Cases | `/cases` | Investigation case management |
| Scans | `/scans` | All scans across cases |
| Reports | `/reports` | Generated case reports |
| Integrations | `/integrations` | API key management and provider health |
| AI Analyst | `/ai` | Chat with an LLM over case context |
| AI Settings | `/settings/ai` | Configure provider, model, and API key |

---

## Dashboard

Shows live metrics:
- Active cases count
- Scans by status (queued / running / completed / error)
- Total indicators discovered
- Recent activity feed

---

## Cases

### Case List (`/cases`)

Displays all investigation cases in a card grid. Filter by status, priority, and date.

**Create a case:** click **New Case** and fill in title, description, priority/severity, case type, assigned analyst, client, jurisdiction, and tags.

### Case Workspace (`/cases/:id`)

The case workspace is the primary investigation surface. It has a fixed header with quick status and severity controls and a tab bar.

---

## Case Workspace Tabs

### Graph

Interactive Cytoscape.js knowledge graph showing:
- **Scan indicators** — nodes discovered by automated OSINT modules (blue/green/amber — by node type)
- **Manual entities** — nodes added by analysts (persons, phones, addresses, social profiles, companies, vehicles, documents)
- **Manual relationships** — edges drawn between any two nodes
- **Scan edges** — relationships discovered by modules

**Toolbar actions:**
- **Add Node** — create a manual entity
- **Add Connected Node** — create a node already linked to a selected node
- **Connect Nodes** — draw a relationship between two existing nodes
- **Scan from node** — launch an OSINT scan directly from a selected node (maps entity type to compatible modules)

**Node panel (right sidebar):**
Clicking any node opens a slide-in panel showing:
- Node type, value, confidence bar
- Metadata key/value pairs
- Linked evidence with preview/download
- Connected edges with linked node labels and source module
- **Scan from this node** — opens the scan modal pre-filled
- **Add timeline event** — log an analyst observation

**Node colors by type:**

| Type | Color |
|---|---|
| domain | Blue |
| ip | Emerald |
| email | Amber |
| breach / threat | Red |
| subdomain | Sky |
| hostname | Violet |
| nameserver | Amber |
| person / alias | Indigo / Purple |
| address | Rose |
| social profile | Yellow |
| company / org | Slate |
| vehicle | Emerald |
| document | Slate |
| port / service | Cyan |
| url / profile_url | Yellow |

---

### Timeline

Chronological event log for the case.

**Event types:** sighting, address observed, phone observed, email observed, account created, profile updated, domain registered, breach observed, scan run, report generated, note added, contact attempt, employment observed, travel or movement, legal event, custom.

**Create an event:** click **+ Event** or use **Add timeline event** from any graph node.

Each event can link to entities, evidence, scans, and relationships. Events with a location entity appear on the Map tab.

---

### Evidence

Evidence library backed by MinIO S3-compatible storage.

**Supported evidence types:** note, URL, screenshot, image, document, PDF, text, scan result, API response, map location, analyst observation.

**Attach evidence:**
- Upload a file (image, PDF, document) — SHA-256 hashed, thumbnail generated for images
- Add a URL source with title and description
- Add a freetext note

**Linking:** evidence items can attach to entities, relationships, timeline events, reports, and scans. One evidence item can link to multiple objects.

**Security:** the frontend never communicates with MinIO directly. All file access goes through backend API routes:
```
GET /api/v1/cases/{id}/evidence/{eid}/download
GET /api/v1/cases/{id}/evidence/{eid}/thumbnail
GET /api/v1/cases/{id}/evidence/{eid}/preview
```

---

### Leads

Review queue for scan-derived findings before they become confirmed facts.

Scan-derived indicators and edges default to `needs_review` status. The Leads tab lets analysts review them before they appear as confirmed objects in the graph and dossier.

**Lead statuses:** needs_review, confirmed, follow_up, stale, rejected.

**Actions per lead:**
- **Confirm** — mark as confirmed; appears in graph and dossier
- **Reject** — hidden from default graph and map (still visible with `include_rejected=true` for audit)
- **Follow up** — flag for later review
- **Promote** — convert a scan indicator into a manual case entity
- **Merge** — combine a scan indicator into an existing manual entity

**Bulk actions:** select multiple leads → bulk confirm, follow-up, stale, or reject (reject asks for confirmation).

---

### Map

Location map for address/location entities, IP geolocation results, and timeline sightings.

**What appears:**
- Manual entities with `latitude`/`longitude` in properties
- IP geolocation evidence (marked as approximate)
- Timeline events linked to a location entity
- Case geolocation observations

**Marker panel:** click any marker to see linked entities, evidence, and timeline events with jump links to those tabs.

**Editing:**
- Manual entity markers can be dragged to reposition; dragging opens the location editor for an explicit save step
- Click **Map** on an unmapped entity in the sidebar to place it on the map
- Create new person, location, or office nodes directly from the map with coordinates prefilled

**Filters:** source type, entity type, confidence, verification status.

---

### Dossier

Intelligence briefing view for the primary case subject.

Sections:
- **Subject hero** — name, role, status, case priority chips
- **Signal metrics** — confirmed entity count, verified relationship count, location count, open lead count
- **Subject profile** — custom properties from the entity tagged as the primary subject
- **Confirmed entities** — grouped by type: people, contact, digital, location, organization, assets
- **Verified relationships** — relationship matrix between confirmed entities
- **Location board** — all mapped locations with precision and confidence badges
- **Timeline highlights** — key confirmed timeline events
- **Evidence locker** — linked evidence summaries (sensitive evidence gated)
- **Open leads** — unresolved review queue items
- **Scan provenance** — scan origins contributing to the dossier

**Subject tagging:** set `properties.subject_profile = true` on a manual entity to make it the dossier primary subject.

**Sensitive evidence:** controlled by the toggle in the dossier header. Sensitive types (legal documents, identity documents, private messages, financial records) are hidden by default.

---

### Scans

Hierarchical list of scans in this case.

- Parent → child indentation
- Status badges (queued / running / completed / error)
- Module list per scan
- Progress bar for running scans
- Launch source badge for node-initiated scans (shows source node label)
- **Create child scan** — launch a new scan under any existing scan

---

### Notes

Investigation notes with add/delete. Supports freetext content.

---

### Reports

Generate and download case reports.

**Formats:** Markdown, Text, HTML, PDF

**Report types:**
- Summary — case overview, scans, indicators, relationships, notes
- Technical — detailed indicator and edge data
- Timeline — chronological event summary
- Dossier — subject profile, confirmed entities, verified relationships, locations, timeline, evidence index, open leads, scan provenance

Reports are **frozen at generation time** (snapshot stored in PostgreSQL). Downloading a report later always returns the same content.

**Download:** click the download icon on any report card. HTML and PDF open inline for preview.

---

## Integration Management (`/integrations`)

Provider cards showing:
- Configured / not configured status
- Last test result
- Enable/disable toggle
- **Test connection** button
- Credential masked hint

**Save a key:** click the card → enter API key → Save. The key is encrypted with Fernet before storage. It is never returned in any API response after save.

**Providers:** Shodan, VirusTotal, AbuseIPDB, Tomba, Hunter, HIBP, IPinfo, AlienVault OTX, Censys, URLScan, Mapbox.

---

## AI Analyst (`/ai`)

Chat interface connected to a configured LLM provider.

**Context options:** current case, current scan, all data.

**Suggested prompts:** Summarize findings, List key indicators, Suggest next investigation steps.

**Configure provider at** `/settings/ai`:
- Provider: Anthropic, OpenAI, Ollama
- Model name
- API key (encrypted at rest)
- Base URL (for Ollama or OpenAI-compatible endpoints)
- Temperature and max tokens
- Test connection

---

## Theme

Toggle dark/light mode from the sidebar bottom button. Theme persists in `localStorage`.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Escape` | Close modal |

---

## Troubleshooting

**Graph is empty after adding a manual entity:**
Refresh the graph tab or click away and back — the graph re-fetches after any entity/relationship mutation.

**Evidence upload fails:**
Check MinIO is running: `docker-compose -f docker-compose.dev.yml ps minio`. Re-run `minio-init` if the bucket is missing:
```bash
docker-compose -f docker-compose.dev.yml run --rm minio-init
```

**Map shows no markers:**
Only entities with `latitude` and `longitude` in their `properties`, or linked geolocation observations, appear on the map. Use **Set Location** from the node panel to add coordinates.

**Dossier shows no subject:**
Tag one manual entity with `properties.subject_profile = true` from the node panel → Edit → Custom Properties.

**Scan from node shows no modules:**
The node type must map to a supported scan target kind (domain, ip, email, url, username, phone, bitcoin). Unsupported types (e.g. `vehicle`, `document`) cannot trigger automated scans.
