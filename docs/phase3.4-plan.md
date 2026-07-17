# OSIF v2.0 - Phase 3.4 Plan: Skip Tracing, Private Investigation Workspace, Manual Graph, Timeline, Evidence, and Maps

**Date:** 2026-07-14  
**Status:** In Progress — Phase 3.4A, 3.4B, 3.4C, and 3.4D complete; Phase 3.4E recommended next
**Focus:** Extend cases from automated OSINT scan containers into full investigation workspaces for skip tracing and private investigation workflows.

---

## Summary

Phase 3.4 should make a case usable for human-led investigations, not only automated scans.

The best direction is to keep one shared **case knowledge graph** underneath the product, while adding separate investigation views that present the same data in different ways:

- Graph view for entity relationships.
- Timeline view for chronology.
- Dossier/profile view for the subject or actor.
- Leads board for review and verification.
- Evidence library for files, images, notes, sources, and citations.
- Map view for locations, addresses, movement, sightings, and geospatial leads.

Manual entities and automated scan results should coexist in the same graph, but every object must preserve provenance:

- Was it manually added by an analyst?
- Was it produced by an automated scan?
- Was it imported from a file?
- Was it returned by a third-party integration?
- Was it AI-suggested and still pending review?

This gives OSIF a strong foundation for skip tracing, private investigation, and enterprise OSINT while retaining the automated scan graph already built in earlier phases.

---

## Product Direction

Do not build a separate skip tracing graph.

Instead:

1. Reuse the existing case graph as the underlying relationship model.
2. Add manual entity creation and manual relationship creation.
3. Add evidence attachments to entities, relationships, timeline events, and findings.
4. Add a timeline model for events and movement over time.
5. Add a map view for location entities and geocoded address events.
6. Add a lead review workflow so automated results do not become confirmed facts without analyst review.
7. Add scan-from-node actions so manual leads can trigger automated enrichment.

This keeps the data model coherent while giving analysts the right UI for different investigation tasks.

---

## Core Investigation Concepts

### Case Subject

A case should be able to define one or more primary subjects.

Examples:

- person
- actor alias
- organization
- company
- online identity
- unknown actor
- infrastructure cluster

Recommended fields:

```text
case_subjects
- id
- case_id
- entity_id
- role
- status
- summary
- created_at
- updated_at
```

Recommended roles:

- primary_subject
- secondary_subject
- associate
- victim
- witness
- organization
- infrastructure_cluster

### Entity

An entity is anything that can appear in a graph, dossier, timeline, evidence link, or scan workflow.

Recommended model:

```text
case_entities
- id
- case_id
- type
- label
- description
- properties
- source_type
- source_ref
- confidence
- verification_status
- visibility
- created_by
- created_at
- updated_at
```

Recommended entity types:

- person
- alias
- username
- email
- phone
- address
- location
- social_profile
- website
- domain
- ip_address
- company
- organization
- vehicle
- document
- image
- account
- crypto_wallet
- device
- event
- note
- unknown

Recommended `source_type` values:

- manual
- scan
- integration
- import
- ai_suggested

Recommended `confidence` values:

- unknown
- low
- medium
- high
- verified

Recommended `verification_status` values:

- lead
- needs_review
- confirmed
- rejected
- stale

### Relationship

Relationships connect two entities.

Recommended model:

```text
case_relationships
- id
- case_id
- from_entity_id
- to_entity_id
- relationship_type
- label
- description
- properties
- source_type
- source_ref
- confidence
- verification_status
- first_seen_at
- last_seen_at
- created_by
- created_at
- updated_at
```

Recommended relationship types:

- uses
- owns
- registered_to
- associated_with
- located_at
- lived_at
- worked_at
- employed_by
- family_of
- connected_to
- communicates_with
- controls
- resolves_to
- hosted_on
- links_to
- mentions
- appears_in
- submitted_by
- observed_at

Every relationship should be able to link to evidence. This is important because in skip tracing and PI workflows, a connection without evidence should remain a lead, not a confirmed fact.

---

## Manual Node Creation

Manual node creation should be a first-class case workflow.

### Required Actions

From the case workspace, analysts should be able to:

- Create a new node manually.
- Create a node connected to an existing node.
- Connect two existing nodes.
- Edit a node.
- Change node type.
- Change confidence.
- Change verification status.
- Attach evidence.
- Add a timeline event from the node.
- Launch an automated scan from the node.
- Convert a scan result into a confirmed node.
- Reject or archive a node.

### Create Node Modal

Fields:

- node type
- label
- description
- confidence
- verification status
- source note
- properties based on type
- evidence attachments
- optional relationship to an existing node
- optional timeline event

Example type-specific properties:

```text
email
- address
- domain
- normalized_address

phone
- number
- country
- e164

address
- street
- city
- region
- postal_code
- country
- latitude
- longitude

social_profile
- platform
- username
- url
- display_name

vehicle
- plate
- state
- make
- model
- year
- color
```

### Create Connected Node Flow

Analyst action:

1. Select a node.
2. Click "Add connected node."
3. Choose relationship type.
4. Choose new node type.
5. Enter new node details.
6. Attach evidence.
7. Save.

Example:

```text
Person: John Doe
  relationship: uses
Email: john@example.com
  evidence: screenshot, note, source URL
  confidence: medium
  status: needs_review
```

This should immediately create:

- the new entity
- the relationship
- optional evidence links
- optional timeline event if the analyst added date context

---

## Manual Relationship Builder

Analysts need a simple way to connect nodes after they already exist.

### UX Options

Support both:

- Graph-based connection: drag from one node to another, then choose relationship type.
- Form-based connection: choose "Connect nodes" and select source, relationship, target.

### Required Relationship Fields

- source node
- target node
- relationship type
- label
- description
- confidence
- verification status
- first seen date
- last seen date
- evidence

### Graph Interaction Rules

- Creating an edge from graph view opens a relationship form before saving.
- Dragging a connection should not create a silent default edge.
- Manual relationships should display a manual badge.
- Scan-created relationships should display an automated/source badge.
- Rejected relationships should be hidden by default but recoverable through filters.

---

## Evidence And Attachment System

Evidence should be reusable across the entire case.

One evidence item should be able to attach to:

- entities
- relationships
- timeline events
- findings
- notes
- reports
- scan results

### Evidence Model

Recommended model:

```text
case_evidence
- id
- case_id
- title
- description
- evidence_type
- source_type
- source_url
- file_name
- file_mime_type
- file_size
- file_sha256
- storage_backend
- storage_key
- thumbnail_storage_key
- captured_at
- collected_by
- chain_of_custody_status
- metadata
- created_at
- updated_at
```

Recommended evidence types:

- note
- url
- screenshot
- image
- document
- pdf
- text
- scan_result
- api_response
- map_location
- analyst_observation

### Attachment Links

Use a link table so evidence can attach to multiple objects.

```text
case_evidence_links
- id
- evidence_id
- target_type
- target_id
- relationship_note
- created_at
```

Recommended `target_type` values:

- entity
- relationship
- timeline_event
- finding
- report
- scan
- indicator
- graph_edge

### Images

Images should be allowed as evidence attachments.

Image handling requirements:

- Store original filename.
- Store MIME type.
- Store file size.
- Store SHA-256 hash.
- Generate thumbnail for UI.
- Preserve original file.
- Avoid exposing MinIO bucket names, object keys, credentials, presigned URLs, or local filesystem paths to the frontend.
- Strip or preserve EXIF based on case policy.
- Show EXIF metadata only when allowed.

Important policy decision:

- For normal UI previews, use sanitized thumbnails.
- For evidence integrity, keep the original file unchanged.
- If EXIF contains sensitive location or device data, show a warning before displaying or exporting it.

### Storage

Phase 3.4B should use MinIO as the primary evidence file backend in Docker.

Recommended Docker services:

- `minio`: S3-compatible object storage for evidence files.
- `minio-init`: one-shot setup container using `minio/mc` to create the evidence bucket and lock down anonymous access.
- `backend`: the only application service that talks to MinIO.
- `frontend`: talks only to the backend evidence API, never to MinIO directly.

Recommended bucket:

```text
osif-evidence
```

Recommended object key layout:

```text
cases/{case_id}/evidence/{evidence_id}/original/{safe_filename}
cases/{case_id}/evidence/{evidence_id}/thumbnail/{safe_filename}
cases/{case_id}/evidence/{evidence_id}/derived/{safe_filename}
```

Recommended backend configuration:

```text
EVIDENCE_STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=osif-evidence
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_REGION=us-east-1
S3_FORCE_PATH_STYLE=true
```

The MinIO console can remain available for administrators, but application setup should not require a person to open the console. Bucket creation should be automated by the Docker setup.

### Backend-Only File Access

The backend must be the only service that reads from or writes to MinIO.

Frontend-facing records should expose backend API paths, not MinIO paths:

```text
GET /api/v1/cases/{case_id}/evidence/{evidence_id}
GET /api/v1/cases/{case_id}/evidence/{evidence_id}/download
GET /api/v1/cases/{case_id}/evidence/{evidence_id}/thumbnail
GET /api/v1/cases/{case_id}/evidence/{evidence_id}/preview
```

The API response can include fields like:

```text
download_url: /api/v1/cases/{case_id}/evidence/{evidence_id}/download
thumbnail_url: /api/v1/cases/{case_id}/evidence/{evidence_id}/thumbnail
preview_url: /api/v1/cases/{case_id}/evidence/{evidence_id}/preview
```

The API response should not include:

- MinIO endpoint URL.
- Bucket name.
- Raw object key when not needed by the UI.
- S3 credentials.
- Presigned MinIO URL unless a later deployment explicitly chooses that pattern.

Preferred implementation:

- Browser uploads evidence to the backend.
- Backend validates file type and size.
- Backend calculates SHA-256 while streaming or before upload.
- Backend writes original file to MinIO.
- Backend generates sanitized thumbnails/previews when supported.
- Backend writes thumbnails/previews to MinIO.
- Backend stores object keys and metadata in PostgreSQL.
- Browser downloads or previews evidence through backend routes.

This design keeps authorization, audit logging, chain-of-custody checks, and report-export filtering inside the backend.

Future production options can still use the same abstraction:

- S3-compatible object storage
- encrypted local volume
- enterprise artifact store

Do not store large binary files directly in PostgreSQL unless there is a clear requirement.

---

## Timeline

Skip tracing needs chronology.

The graph tells what is connected. The timeline tells when something happened.

### Timeline Event Model

```text
case_timeline_events
- id
- case_id
- title
- description
- event_type
- occurred_at
- occurred_at_precision
- start_at
- end_at
- timezone
- location_entity_id
- confidence
- verification_status
- source_type
- source_ref
- created_by
- created_at
- updated_at
```

Recommended `occurred_at_precision` values:

- exact
- date
- month
- year
- approximate
- unknown

Recommended event types:

- sighting
- address_observed
- phone_observed
- email_observed
- account_created
- profile_updated
- domain_registered
- breach_observed
- scan_run
- report_generated
- note_added
- contact_attempt
- employment_observed
- travel_or_movement
- legal_event
- custom

### Timeline Links

Timeline events should link to:

- entities
- relationships
- evidence
- scans
- findings

Recommended link model:

```text
case_timeline_links
- id
- timeline_event_id
- target_type
- target_id
- created_at
```

### Timeline UX

Required views:

- chronological list
- grouped by month/year
- filter by entity
- filter by event type
- filter by confidence/status
- show evidence count
- show linked entities
- create event from node
- create event from evidence
- create event from scan result

Useful PI features:

- "Known address history" timeline.
- "Online activity" timeline.
- "Infrastructure activity" timeline.
- "Case activity" timeline.

---

## Map View

Yes, location entities should have a mapping experience.

The map should not replace the graph. It should be another view over the same case data.

### What Appears On The Map

Map-visible objects:

- location entities
- address entities with coordinates
- timeline events with a location
- sightings
- known address history
- business or organization locations
- IP geolocation results, clearly marked as approximate
- scan-discovered locations, clearly marked as automated/low-confidence unless verified

### Location Model

Location data can live inside entity properties, but a normalized table is better once map workflows grow.

Recommended model:

```text
case_locations
- id
- case_id
- entity_id
- label
- address_text
- latitude
- longitude
- precision
- geocoding_source
- confidence
- verification_status
- metadata
- created_at
- updated_at
```

Recommended `precision` values:

- exact
- building
- street
- city
- region
- country
- ip_geo_approximate
- unknown

### Map UX

Required features:

- Case map tab.
- Marker clustering for many locations.
- Different marker icons by entity type.
- Confidence and status badges on marker popups.
- Link marker to graph node, timeline events, and evidence.
- Filter by entity type, source type, confidence, and time range.
- Draw line/path view for chronological movement when supported by evidence.
- Clear warning for approximate IP geolocation.

### Geocoding

Geocoding should be optional and provider-configurable.

Phase 3.4 can support:

- manual latitude/longitude entry
- manual address entry without geocoding
- optional geocoding provider later through the integration settings system

Do not silently send private addresses to a third-party geocoding provider. If geocoding is enabled, show that the address will be submitted externally.

### Mapping Library Direction

Recommended frontend direction:

- Use a web map component in the case workspace.
- Start with a simple 2D map.
- Keep provider choice configurable.
- Verify map tile provider terms before production use.

Implementation options:

- Leaflet-style raster map for fastest implementation.
- MapLibre-style vector map if offline/private tiles or advanced styling become important.

For enterprise/private investigation deployments, support for self-hosted or private tiles should be considered later.

---

## Scan From Node

Manual entities should be able to trigger automated OSINT workflows.

Examples:

| Node Type | Available Actions |
|---|---|
| domain | Run Domain Recon Bot, DNS, WHOIS/RDAP, CT logs, urlscan |
| IP address | Run IP Reputation Bot, AbuseIPDB, Shodan, GreyNoise, IPinfo |
| URL | Run URL/Phishing Triage Bot, urlscan, URLhaus, PhishTank |
| email | Run Email Exposure Bot, HIBP if configured, domain extraction |
| phone | Run phone enrichment only if configured and legally appropriate |
| social username | Run username/profile discovery only if provider exists and policy allows |
| address/location | Create map/timeline context; external enrichment requires explicit provider and approval |
| company/domain | Run Company Footprint Bot |

### Scan Result Handling

Automated scan results should not immediately become confirmed facts.

Recommended workflow:

```text
manual node
-> run enrichment
-> create scan result entities/relationships as leads
-> analyst reviews
-> analyst promotes, edits, or rejects
-> confirmed objects appear in dossier/reports
```

### Review Queue

Scan-created items should land in a review queue with:

- source provider
- source module
- confidence
- why it matched
- evidence
- promote action
- reject action
- merge with existing node action

This is important for skip tracing because false positives are common.

---

## Dossier View

The subject profile should be a readable investigator workspace.

### Dossier Sections

For a person or actor:

- summary
- aliases
- known emails
- known phones
- known addresses
- known locations
- social profiles
- associated people
- associated organizations
- employment or company links
- vehicles
- online infrastructure
- key timeline
- evidence
- open leads
- confirmed findings

For an organization:

- domains
- websites
- emails
- employees or associated people
- infrastructure
- locations
- technology profile
- reports
- timeline

### Dossier Rules

- Show confirmed data first.
- Show leads separately.
- Never hide confidence.
- Every claim should link to evidence.
- Analyst notes should be clearly separate from scan output.

---

## Leads Board

Add a lead workflow between raw data and confirmed findings.

Recommended statuses:

- new
- needs_review
- follow_up
- confirmed
- rejected
- stale

Lead sources:

- manual node
- automated scan result
- imported file
- AI suggestion
- evidence extraction

Lead actions:

- promote to entity
- attach to existing entity
- create relationship
- create timeline event
- reject
- mark follow-up
- run scan

This prevents the graph from becoming polluted with unverified results.

---

## UI Plan

### Case Workspace Tabs

Recommended case tabs:

- Overview
- Graph
- Timeline
- Dossier
- Leads
- Evidence
- Map
- Scans
- Reports

If the tab count becomes too large, group investigation tabs under an "Investigation" section.

### Graph View Changes

Add:

- manual node creation button
- add connected node action
- connect existing nodes action
- edge creation form
- source badges
- confidence filters
- verification filters
- manual vs automated filters
- scan-from-node menu
- evidence count badge on nodes/edges

### Timeline View

Add:

- event creation
- filters
- linked entity chips
- evidence previews
- map jump for located events
- graph jump for linked entities

### Evidence View

Add:

- upload evidence
- add URL evidence
- add note evidence
- image preview
- file metadata
- hash display
- linked objects
- filter by evidence type
- attach to node/relationship/event/finding

### Map View

Add:

- marker list side panel
- marker popup with linked entities
- timeline range filter
- confidence/status filters
- graph jump
- timeline jump
- evidence jump

---

## API Plan

Recommended endpoints:

```text
GET    /api/v1/cases/{case_id}/entities
POST   /api/v1/cases/{case_id}/entities
GET    /api/v1/cases/{case_id}/entities/{entity_id}
PUT    /api/v1/cases/{case_id}/entities/{entity_id}
DELETE /api/v1/cases/{case_id}/entities/{entity_id}

GET    /api/v1/cases/{case_id}/relationships
POST   /api/v1/cases/{case_id}/relationships
PUT    /api/v1/cases/{case_id}/relationships/{relationship_id}
DELETE /api/v1/cases/{case_id}/relationships/{relationship_id}

GET    /api/v1/cases/{case_id}/timeline
POST   /api/v1/cases/{case_id}/timeline
PUT    /api/v1/cases/{case_id}/timeline/{event_id}
DELETE /api/v1/cases/{case_id}/timeline/{event_id}

GET    /api/v1/cases/{case_id}/evidence
POST   /api/v1/cases/{case_id}/evidence
GET    /api/v1/cases/{case_id}/evidence/{evidence_id}
PUT    /api/v1/cases/{case_id}/evidence/{evidence_id}
DELETE /api/v1/cases/{case_id}/evidence/{evidence_id}

POST   /api/v1/cases/{case_id}/evidence/{evidence_id}/links
DELETE /api/v1/cases/{case_id}/evidence/{evidence_id}/links/{link_id}

GET    /api/v1/cases/{case_id}/map
POST   /api/v1/cases/{case_id}/entities/{entity_id}/scan
```

Graph endpoint should merge:

- existing indicators and edges from scans
- manual entities
- manual relationships
- reviewed/promoted scan leads

But the API response should preserve source type so the UI can filter and style correctly.

---

## Data Migration Strategy

The existing graph likely uses indicators and graph edges from scans.

Phase 3.4 should avoid breaking that behavior.

Recommended migration approach:

1. Add new tables for manual entities, relationships, timeline events, evidence, and locations.
2. Update graph endpoint to include both old scan graph objects and new manual graph objects.
3. Add stable frontend graph node IDs with prefixes:
   - `indicator:{id}`
   - `entity:{id}`
   - `relationship:{id}`
   - `scan:{id}`
4. Add source metadata to graph responses.
5. Later, consider unifying scan indicators into case entities if the model proves stable.

This avoids a dangerous rewrite of existing automated scan graph behavior.

---

## Reporting Changes

Reports should support PI-style outputs.

Add report sections:

- subject dossier
- verified identities
- aliases
- known contact points
- address history
- map/location summary
- timeline
- key relationships
- evidence index
- open leads
- rejected leads, optional
- automated scan summary
- analyst notes

Report rules:

- Confirmed facts and open leads must be separated.
- Evidence citations should appear next to important claims.
- Location precision must be disclosed.
- IP geolocation should be marked approximate.
- Sensitive evidence should be excluded unless explicitly selected.

---

## Compliance And Safety

Skip tracing and private investigation workflows can involve sensitive personal data. OSIF should support legitimate, authorized investigations and avoid workflows that encourage unsafe or unlawful use.

Required controls:

- case purpose field
- data sensitivity label
- external submission warnings
- evidence source tracking
- audit events for manual changes
- audit events for evidence upload/download
- audit events for scan-from-node actions
- clear distinction between lead and confirmed fact
- redaction for reports
- no hidden third-party enrichment

Recommended case sensitivity labels:

- public
- internal
- confidential
- sensitive_personal_data
- restricted

Before production use, legal and policy requirements should be reviewed for the deployment context.

---

## Implementation Order

### Step 1: Manual Entities And Relationships — Done

- [x] Add case entity model/schema/migration.
- [x] Add case relationship model/schema/migration.
- [x] Add CRUD endpoints.
- [x] Add manual node creation UI.
- [x] Add connect existing nodes UI.
- [x] Add connected-node creation flow.
- [x] Update graph endpoint to include manual nodes and edges.

### Step 2: Evidence Attachments — Done

- [x] Add evidence model and evidence link model.
- [x] Add MinIO service to Docker Compose.
- [x] Add MinIO init service/script to create the evidence bucket automatically.
- [x] Add backend storage service abstraction with MinIO/S3 implementation.
- [x] Add upload endpoint.
- [x] Add backend download, thumbnail, and preview endpoints.
- [x] Add URL/note evidence creation.
- [x] Add file hash generation.
- [x] Add image thumbnail generation.
- [x] Add evidence panel on nodes and relationships.
- [x] Show linked evidence indication and preview/download actions in the graph node sidebar.

### Step 3: Timeline — Done

- [x] Add timeline event model.
- [x] Add timeline link model.
- [x] Add timeline CRUD endpoints.
- [x] Add timeline tab.
- [x] Add create timeline event from node/evidence/scan result.

### Step 4: Map View — Done

- [x] Add location model or normalized location properties.
- [x] Add map endpoint.
- [x] Add map tab.
- [x] Add manual latitude/longitude support.
- [x] Add marker filtering.
- [x] Add timeline and graph links from map markers.

### Step 5: Leads And Review

- [ ] Add lead status to manual and scan-derived objects.
- [ ] Add review queue.
- [ ] Add promote/reject/merge actions.
- [ ] Keep automated scan results as leads until confirmed.

### Step 6: Scan From Node

- [ ] Add node action menu.
- [ ] Map entity types to available scan workflows.
- [ ] Create scan runs from selected node values.
- [ ] Write scan results back as leads with source metadata.

### Step 7: Dossier And PI Reports

- [ ] Add subject dossier tab.
- [ ] Add report sections for timeline, evidence, locations, and verified relationships.
- [ ] Add include/exclude controls for sensitive evidence.

---

## Testing Plan

### Backend

- Create/update/delete manual entity.
- Create connected node and relationship in one request.
- Connect two existing nodes.
- Attach evidence to entity.
- Attach evidence to relationship.
- Upload image and generate thumbnail.
- Create timeline event linked to entities and evidence.
- Map endpoint returns only location-capable objects.
- Scan-from-node creates a scan with correct target.
- Rejected leads do not appear as confirmed facts.

### Frontend

- Manual node appears on graph.
- Manual relationship appears on graph.
- Graph filters separate manual, scan, and confirmed data.
- Evidence upload attaches to a node.
- Timeline event renders in chronological order.
- Map marker opens linked entity/evidence/timeline details.
- Scan-from-node action is visible only for supported node types.
- Dossier separates confirmed data from leads.

### Security And Privacy

- File upload rejects unsafe types.
- File download requires case access.
- Evidence APIs do not expose MinIO credentials, bucket internals, object storage URLs, or local filesystem paths.
- Frontend evidence downloads and previews go through backend API paths only.
- Deleted evidence links do not delete the original evidence unless explicitly requested.
- External geocoding cannot run silently.
- Sensitive evidence is excluded from reports unless selected.

---

## Definition Of Done

- Analysts can manually create case nodes.
- Analysts can create a new node connected to an existing node.
- Analysts can connect two existing nodes with a typed relationship.
- Manual and automated graph objects can be filtered separately.
- Entities and relationships can have evidence attachments.
- Images can be uploaded, previewed, hashed, and linked to graph objects.
- Timeline events can be created manually and linked to entities/evidence.
- Location/address entities can appear on a map.
- The map links back to graph, timeline, and evidence.
- Manual nodes can trigger supported automated scans.
- Scan results from manual nodes enter a review flow before becoming confirmed facts.
- Dossier view summarizes the subject with confirmed facts, open leads, evidence, timeline, and locations.
- PI-style reports can include dossier, timeline, evidence, map/location summary, and relationship findings.

---

## Implementation Log

**Last updated:** 2026-07-16

### ✅ Plan A — Manual Entities, Manual Relationships, And Graph Merge

Implemented the first Phase 3.4 slice:

- Added `case_entities` table for manual investigation nodes.
- Added `case_relationships` table for manual links between case graph nodes.
- Manual relationships can connect:
  - manual entity to manual entity
  - manual entity to automated scan indicator
  - automated scan indicator to manual entity
- Added backend CRUD endpoints:
  - `GET/POST /api/v1/cases/{case_id}/entities`
  - `PUT/DELETE /api/v1/cases/{case_id}/entities/{entity_id}`
  - `GET/POST /api/v1/cases/{case_id}/relationships`
  - `PUT/DELETE /api/v1/cases/{case_id}/relationships/{relationship_id}`
- Updated `/api/v1/cases/{case_id}/graph` to merge:
  - automated scan indicators and edges
  - manual entities
  - manual relationships
- Manual-only cases now return graph nodes even before scans exist.
- Added graph UI actions:
  - Add Node
  - Add Connected Node
  - Connect Nodes
- Added manual node form fields:
  - type
  - label
  - value
  - description
  - confidence
  - verification status
  - optional relationship type when creating a connected node
- Added visual support for PI/skip-tracing node types:
  - person
  - alias
  - address
  - social profile
  - company
  - vehicle
  - document

Validation completed:

- Frontend production build passes.
- Python syntax check passes for new backend files.
- Alembic migration `c7b1d9a2f4e8_add_case_entities_and_relationships.py` applied successfully in Docker.
- Backend health endpoint returns `ok`.
- Temporary API smoke test created a case, added manual entities, connected nodes, verified the merged graph, and deleted the temporary case.

Browser visual testing note:

- The in-app browser automation surface was unavailable in this session, so visual click-through testing could not be completed through Browser.

### Plan B — MinIO Evidence Attachments

Implemented the evidence attachment foundation:

- Added MinIO-backed evidence file storage in Docker.
- Added automated bucket initialization through the Docker setup.
- Added backend-only upload, download, thumbnail, and preview routes.
- Added URL, note, file, image, PDF, and document evidence support.
- Added SHA-256 file hashing and image thumbnail generation.
- Added reusable evidence links for entities, relationships, indicators, graph edges, timeline events, reports, scans, notes, and cases.
- Added evidence library UI.
- Added graph node sidebar evidence indication, linked evidence list, preview, download, and attach actions.
- Confirmed frontend talks to backend evidence API paths only, not directly to MinIO.

Validation completed:

- Frontend production build passed.
- Python syntax checks passed.
- Docker stack ran with MinIO and backend services.
- Evidence upload, list, download, link-to-entity, and case deletion cleanup smoke tests passed.

### Plan C — Case Timeline Events

Implemented the timeline foundation:

- Added `case_timeline_events` and `case_timeline_links`.
- Added timeline CRUD endpoints under `/api/v1/cases/{case_id}/timeline`.
- Added timeline tab in the case workspace.
- Added manual timeline event creation.
- Added timeline creation from graph nodes, evidence, and scan rows.
- Added timeline links to entities, evidence, scans, indicators, graph edges, notes, relationships, and cases.
- Added distinct timeline icons for case activity, scans, reports, notes, evidence, sightings, address observations, contact attempts, movement, legal events, and custom events.
- Added evidence support for linking directly to timeline events.

Validation completed:

- Frontend production build passed.
- Python syntax checks passed.
- Alembic migration `a3d8e4f9c2b7_add_case_timeline_events.py` applied successfully in Docker.
- API smoke test created, filtered, updated, linked, and deleted timeline events.

### Plan D — Case Map View

Implemented the first map workspace slice:

- Added `GET /api/v1/cases/{case_id}/map`.
- Built normalized map markers from:
  - manual entities with `latitude` and `longitude` in `properties`
  - evidence records with map coordinates in metadata
  - timeline events linked to location entities
  - scan-derived geolocation evidence such as IP geolocation results
- Added unmapped queues for address/location-capable objects missing coordinates.
- Added manual coordinate fields to the manual node modal:
  - map label
  - latitude
  - longitude
  - location precision
- Added timeline location selection so sightings, address observations, movement, and other events can plot through a location entity.
- Added a full-height Map tab with:
  - marker index
  - operations-map canvas
  - marker detail panel
  - source, status, and type filters
  - confidence, precision, status, and source badges
  - approximate-location warnings
  - linked graph/evidence/timeline targets
  - attach evidence and add timeline actions from a marker
- Added a Mapbox token readiness indicator using `VITE_MAPBOX_TOKEN`.
- Added Mapbox GL rendering when `VITE_MAPBOX_TOKEN` is configured.
- Current implementation falls back to a static operations-map canvas when no Mapbox token is configured.

Validation completed:

- `python3 -m py_compile backend/app/api/v1/case_graph.py` passed.
- `npm --prefix frontend run build` passed.

### Next Slice

Recommended Plan E:

- Leads and review workflow:
  - lead board
  - promote/reject/merge actions
  - scan result review queue
  - separation of confirmed facts from unverified leads across graph, map, reports, and dossier
