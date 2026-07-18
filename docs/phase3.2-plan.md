# OSIF v2.0 - Phase 3.2 Plan: Enterprise Case Workflow, Reports, Integrations, and AI Settings

**Date:** 2026-07-01  
**Status:** Planning  
**Focus:** Make Phase 3.1 case workflows operationally useful for enterprise OSINT while moving user-configurable API and AI settings out of `.env`.

---

## Summary

Phase 3.2 should focus on four practical gaps:

- Case records need editable metadata, status transitions, and severity/priority controls from the UI.
- Reports need server-side HTML and PDF exports, not only markdown/text blob downloads in the browser.
- Integrations should move from `.env`-only API keys to encrypted database-backed credentials with environment fallback during migration.
- AI settings should become configurable through the app and stored in PostgreSQL, with secrets encrypted at rest.

The best course is **not** to remove `.env` entirely. Keep `.env` for bootstrap and infrastructure values such as `DATABASE_URL`, Redis, JWT signing, and the encryption key. Store analyst-managed OSINT API keys and AI provider settings in PostgreSQL.

---

## Phase 3.2 Objectives

- Add complete case editing and workflow controls.
- Support report formats: `markdown`, `text`, `html`, and `pdf`.
- Add a database-backed settings and secrets layer.
- Keep OSINT modules compatible while migrating them away from direct `os.getenv(...)` calls.
- Add setup/admin workflows for entering, testing, rotating, and disabling integration credentials.
- Add AI provider configuration in the UI with database persistence.
- Preserve enterprise basics: auditability, no secret leakage in responses, safe fallbacks, and predictable migrations.

---

## Non-Goals

- Do not build full RBAC in this phase unless it already exists by the time implementation starts.
- Do not store database credentials, Redis settings, JWT secrets, or encryption keys in the database.
- Do not make API keys readable again after save. UI should show configured status and masked hints only.
- Do not make the CLI write directly to PostgreSQL as the default path. Prefer backend API endpoints so validation, encryption, and audit logging stay centralized.

---

## Architecture Decision: `.env` vs PostgreSQL

### Keep In `.env`

These are bootstrap settings required before the database can be reached or decrypted:

- `DATABASE_URL`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
- `SECRET_KEY`
- `JWT_ALGORITHM`
- `APP_ENCRYPTION_KEY`
- `CORS_ORIGINS`
- Optional deployment/runtime values such as `API_HOST`, `API_PORT`, worker concurrency, debug flags

### Move To PostgreSQL

These are operator-managed application settings:

- OSINT provider keys: Shodan, VirusTotal, AbuseIPDB, Tomba, Hunter, IPinfo, AlienVault OTX, Censys, URLScan, etc.
- AI provider selection: Anthropic, OpenAI, Ollama
- AI model, base URL, temperature, max tokens, timeout
- Per-provider enabled/disabled flags
- Integration health state and last test result

### Compatibility Strategy

For Phase 3.2, use a compatibility provider:

1. Read encrypted value from PostgreSQL first.
2. If no DB value exists, fall back to existing `.env` variable.
3. Return only booleans or masked values through API responses.
4. Emit a warning or migration hint when `.env` fallback is used.
5. In a later phase, disable `.env` fallback with a deployment flag.

This lets current Docker, CLI, and worker flows keep running while the application moves toward database-managed credentials.

---

## 1. Case Editing and Workflow Controls

### Current State

- Backend already has `PUT /api/v1/cases/{case_id}` using `CaseUpdate`.
- Backend has `PATCH /api/v1/cases/{case_id}/status`.
- Case schema supports `status`, `priority`, `assigned_to`, `client`, `jurisdiction`, target metadata, and tags.
- UI displays status and priority but lacks a complete edit workflow.

### Required UX

- Add an **Edit Case** action in `CaseDetail.vue`.
- Add a case edit modal or right-side drawer with:
  - title
  - description
  - status
  - priority/severity
  - assigned analyst
  - client
  - jurisdiction
  - case type
  - target name
  - target aliases
  - target location
  - target date of birth
  - tags
- Add quick controls in the case header:
  - status dropdown
  - priority/severity dropdown
  - assigned analyst field
- Add edit action from `CasesList.vue`.
- Refresh case list/detail state after updates.

### Recommended Naming

The model currently uses `priority`. The user-facing label can be **Severity** if that fits the OSINT workflow better, but avoid adding a duplicate `severity` column immediately.

Recommended Phase 3.2 approach:

- Keep DB field: `priority`
- UI label: `Severity`
- Values: `critical`, `high`, `medium`, `low`
- Later phase can add a separate `impact` or `risk_score` if needed.

### Status Workflow

Use a clear status set:

- `open`
- `active`
- `closed`
- `archived`

Rules:

- Changing to `closed` sets `closed_at` if empty.
- Reopening a case clears `closed_at`.
- Archived cases should be read-only by default in the UI unless explicitly edited.
- Deleting a case should remain a deliberate destructive action, not part of the normal status workflow.

### Backend Additions

- Add `PATCH /api/v1/cases/{case_id}` for partial updates, or keep using `PUT` but call it consistently from the UI.
- Add focused endpoints only if useful:
  - `PATCH /api/v1/cases/{case_id}/status`
  - `PATCH /api/v1/cases/{case_id}/priority`
  - `PATCH /api/v1/cases/{case_id}/assignment`
- Add validation constants for status and priority instead of duplicating regex strings.
- Add audit events for case updates when audit logging exists.

### Frontend Files

- `frontend/src/views/CaseDetail.vue`
- `frontend/src/views/CasesList.vue`
- `frontend/src/stores/cases.js`
- `frontend/src/api/client.js`
- New component: `frontend/src/components/CaseEditModal.vue`

### Acceptance Criteria

- Analyst can edit a case from detail view.
- Analyst can change case status without leaving the page.
- Analyst can change severity/priority without leaving the page.
- Case header, case list, and dashboard reflect updates after save.
- Closing a case sets `closed_at`; reopening clears it.

---

## 2. HTML and PDF Reports

### Current State

- Report model has `report_format` and `content`.
- Backend generates deterministic markdown/text content.
- Frontend downloads markdown/text from the browser.
- Supported formats are currently effectively `markdown` and `text`.

### Required Formats

- `markdown`
- `text`
- `html`
- `pdf`

### Recommended Backend Design

Create a report rendering service:

`backend/app/services/report_renderer.py`

Responsibilities:

- Build a normalized report context from case, scans, indicators, edges, notes, and timeline.
- Render markdown/text from the context.
- Render HTML through a template.
- Render PDF from the same HTML template.
- Return bytes, filename, and MIME type for download endpoints.

Recommended endpoint additions:

- `POST /api/v1/cases/{case_id}/reports`
  - Still creates a persisted report record.
  - Accepts `report_format` values `markdown`, `text`, `html`, `pdf`.
- `GET /api/v1/reports/{report_id}/download`
  - Returns `StreamingResponse` or `Response` with correct `Content-Type` and `Content-Disposition`.
- `GET /api/v1/reports/{report_id}/preview`
  - Returns HTML for browser preview when format is `html` or `pdf`.

### PDF Library Choice

Prefer an HTML-to-PDF renderer if the deployment can support it:

- Best output: Playwright/Chromium print-to-PDF
- Simpler Python-only fallback: WeasyPrint, if system dependencies are acceptable
- Minimal fallback: ReportLab for plain, less polished PDFs

Recommended course:

1. Implement HTML report templates first.
2. Generate PDF from HTML.
3. If Chromium is too heavy for Docker, use a ReportLab fallback for Phase 3.2 and keep Chromium PDF as Phase 3.3.

### Storage Choice

For Phase 3.2, store canonical report content and metadata in PostgreSQL. Generate downloadable bytes on demand.

Optional fields to add later:

- `rendered_content_type`
- `rendered_size_bytes`
- `template_id`
- `snapshot`

Do not store large binary PDFs in PostgreSQL unless there is a clear retention requirement. If persistent binary artifacts become necessary, use object storage or a filesystem-backed artifact service.

### Frontend Changes

- Update report generation form in `CaseDetail.vue`:
  - report type
  - format: markdown/text/html/pdf
  - title
- Update `ReportsView.vue`:
  - show format badge
  - preview HTML reports
  - download via backend `/download` endpoint
- Stop creating PDF/HTML blobs only in the browser. Backend must own export generation.

### Acceptance Criteria

- Markdown and text still work.
- HTML report downloads as non-empty `.html`.
- PDF report downloads as non-empty `.pdf`.
- Downloaded filenames use safe names.
- Correct MIME types are returned.
- Report content is deterministic and includes case metadata, scans, indicators, relationships, timeline, and notes.

---

## 3. Database-Backed Integrations

### Current State

- `backend/app/api/v1/integrations.py` returns a static catalog.
- Configured status is based on `os.getenv(integration["env_var"])`.
- Several modules read API keys directly with `os.getenv(...)`.

### Best Course

Add a database-backed integration credential system and migrate modules to use a shared provider instead of direct environment reads.

### New Models

`backend/app/models/integration.py`

```python
class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    id = ...
    provider = ...              # shodan, virustotal, tomba, etc.
    display_name = ...
    enabled = ...
    encrypted_config = ...      # JSON object encrypted as one payload, or encrypted fields
    masked_hint = ...           # e.g. last 4 chars or key prefix metadata only
    source = ...                # db, env_imported, disabled
    last_tested_at = ...
    last_test_status = ...
    last_test_message = ...
    created_at = ...
    updated_at = ...
```

Use `provider` as a unique key for global settings in Phase 3.2.

Possible later extension:

- tenant-scoped credentials
- user-scoped credentials
- case-scoped override credentials

### Encryption

Add an application encryption utility:

`backend/app/core/crypto.py`

Requirements:

- Use authenticated encryption.
- Use `APP_ENCRYPTION_KEY` from `.env`.
- Do not log plaintext secrets.
- Do not return plaintext secrets from API responses.
- Provide key rotation plan documentation.

Python package options:

- `cryptography` with Fernet/MultiFernet
- envelope encryption later if KMS is introduced

### Credential Provider

Add a service:

`backend/app/services/credentials.py`

Responsibilities:

- `get_secret(provider, field)`
- `get_config(provider)`
- DB-first lookup
- `.env` fallback during migration
- optional short TTL cache
- cache invalidation after updates

OSINT modules should stop calling `os.getenv(...)` directly and use this provider.

Because most modules are synchronous today, implementation options are:

- Convert module execution path to pass a credential context into each module.
- Or provide a preloaded credential map to the scan worker before running modules.
- Avoid doing async DB calls deep inside synchronous module code.

Recommended Phase 3.2 implementation:

1. Worker loads credentials once at scan start.
2. Pass `credential_provider` or `credentials` into module execution context.
3. Update modules incrementally:
   - Shodan
   - VirusTotal
   - AbuseIPDB
   - Tomba
   - Hunter
   - URLScan

### Integration API

Add endpoints:

- `GET /api/v1/integrations`
  - catalog plus configured/enabled/health status
- `GET /api/v1/integrations/{provider}`
  - metadata and masked config only
- `PUT /api/v1/integrations/{provider}`
  - save or update encrypted config
- `POST /api/v1/integrations/{provider}/test`
  - verify credentials without running a full scan
- `POST /api/v1/integrations/import-env`
  - one-time import from `.env` into DB
- `DELETE /api/v1/integrations/{provider}`
  - remove stored DB credential

### Setup Flow

Add a setup/admin workflow:

1. On first run, backend starts with `.env` bootstrap settings only.
2. Database migrations create settings tables.
3. Setup page shows integrations and AI providers.
4. Operator enters API keys in UI.
5. Backend encrypts values and stores them in PostgreSQL.
6. Operator can test each provider.
7. Modules use DB credentials on the next scan.

### CLI Compatibility

The CLI should not become a direct PostgreSQL secret writer by default.

Recommended CLI approach:

- CLI reads its own `.env` or config file only for CLI runtime needs.
- CLI can call backend APIs to manage credentials:
  - `osif integrations set shodan`
  - `osif integrations test shodan`
  - `osif integrations import-env`
- Backend handles encryption, validation, and audit logging.

Optional admin-only fallback:

- A backend management command can import `.env` keys into PostgreSQL for offline setup.
- Direct DB writes should be treated as maintenance tooling, not the normal CLI path.

### Acceptance Criteria

- Integration list shows DB-configured status.
- Existing `.env` keys still work as fallback.
- Saving a key in UI makes scans use that DB key.
- API responses never expose plaintext API keys.
- A provider test can pass/fail without creating a scan.
- At least Shodan, VirusTotal, AbuseIPDB, Tomba, and URLScan are migrated away from direct `os.getenv(...)`.

---

## 4. Configurable AI Settings

### Current State

- `backend/app/api/v1/ai.py` reads provider, model, key, temperature, and max tokens from `os.getenv(...)`.
- `AiSettingsView.vue` displays instructions for `.env`.
- There is no persistent UI configuration path.

### New Model

`backend/app/models/app_setting.py` or `backend/app/models/ai_setting.py`

Recommended model:

```python
class AISetting(Base):
    __tablename__ = "ai_settings"

    id = ...
    provider = ...              # anthropic, openai, ollama
    model = ...
    enabled = ...
    encrypted_api_key = ...     # null for ollama
    base_url = ...              # useful for Ollama/OpenAI-compatible providers
    temperature = ...
    max_tokens = ...
    timeout_seconds = ...
    is_default = ...
    last_tested_at = ...
    last_test_status = ...
    created_at = ...
    updated_at = ...
```

Rules:

- Only one setting should be `is_default = true`.
- Ollama can be enabled without an API key.
- API keys are encrypted and never returned.
- Responses return `has_api_key`, `masked_hint`, and non-secret config.

### AI API

Add or replace endpoints:

- `GET /api/v1/ai/settings`
  - return active/default AI settings without plaintext secret
- `PUT /api/v1/ai/settings`
  - update default provider/model/options/API key
- `GET /api/v1/ai/providers`
  - static provider catalog and suggested models
- `POST /api/v1/ai/test`
  - test configured provider with a small request
- `POST /api/v1/ai/analyze`
  - use DB settings first, `.env` fallback while migrating

### Frontend UX

Update `AiSettingsView.vue`:

- Provider selector
- Model field or model dropdown
- API key input with "replace key" behavior
- Base URL field for Ollama/OpenAI-compatible endpoints
- Temperature and max token controls
- Test connection button
- Save button
- Configured/missing status
- Clear warning when `.env` fallback is active

### AI Analysis Safety

Before sending case data to external LLMs:

- Show which provider is active.
- Add a "redact sensitive fields" setting.
- Add future support for cited answers tied to graph evidence.
- Log provider, model, case_id, scan_id, and token settings, but never prompt secrets.

### Acceptance Criteria

- AI settings can be saved from the UI.
- `/api/v1/ai/analyze` uses database settings.
- `.env` AI settings still work if no DB settings exist.
- API key is never returned after save.
- Ollama works with configurable `base_url`.
- Provider test reports success/failure in the UI.

---

## Migration Plan

### Migration 1: Case Workflow Cleanup

If no DB schema changes are needed for case editing, skip this migration.

Possible additions:

- `cases.closed_reason`
- `cases.review_status`
- `cases.updated_by`

Only add these if they are used in the UI during Phase 3.2.

### Migration 2: Integrations

Create:

- `integration_credentials`

Indexes:

- unique index on `provider`
- index on `enabled`

### Migration 3: AI Settings

Create:

- `ai_settings`

Indexes:

- unique partial index for default setting if supported
- index on `provider`
- index on `enabled`

### Migration Rules

- Import every new model in `backend/alembic/env.py`.
- Import every new model in `backend/app/models/__init__.py`.
- Do not create empty Alembic revisions.
- Name all constraints explicitly.
- Run migrations inside Docker before testing endpoints.

---

## Implementation Order

### Step 1: Case Edit UX

- Build `CaseEditModal.vue`.
- Add API/store methods for case update.
- Add header status and severity controls.
- Verify case list/detail/dashboard refresh correctly.

### Step 2: Report Renderer

- Extract current report generation into a service.
- Add HTML renderer.
- Add backend download endpoint.
- Add PDF renderer or PDF fallback.
- Update frontend download flow.

### Step 3: Secrets Foundation

- Add encryption utility.
- Add integration credential model/schema/migration.
- Add credential provider service.
- Add integration CRUD/test endpoints.
- Keep `.env` fallback.

### Step 4: Migrate OSINT Modules

- Update modules that require API keys to use the provider/context.
- Start with highest-value integrations:
  - Shodan
  - VirusTotal
  - AbuseIPDB
  - Tomba
  - URLScan
- Add tests for DB-first and `.env` fallback behavior.

### Step 5: AI Settings

- Add AI settings model/schema/migration.
- Update AI endpoints to read DB first.
- Update AI Settings UI to save/test settings.
- Add Ollama `base_url` support in DB.

### Step 6: Setup Experience

- Add first-run setup route or admin settings area.
- Add `.env` import action.
- Add "configured from DB" vs "using environment fallback" indicators.

---

## Testing Plan

### Backend

- Case update endpoint tests:
  - edit title/description/tags
  - status close/reopen
  - priority/severity changes
- Report tests:
  - markdown content non-empty
  - text content non-empty
  - HTML content valid and non-empty
  - PDF response non-empty and correct MIME
- Integration tests:
  - save credential
  - list masks secrets
  - DB value overrides `.env`
  - `.env` fallback works
  - disabled credential is not used
- AI tests:
  - DB settings override `.env`
  - missing key returns controlled 503
  - Ollama base URL is respected

### Frontend

- Case edit modal saves and refreshes UI.
- Status/severity dropdowns update badges.
- Report form supports all four formats.
- Report download uses backend response and correct extension.
- Integrations page can save/test credentials without showing secret values.
- AI settings page can save/test provider settings.

### Manual Docker Verification

- `docker-compose -f docker-compose.dev.yml up -d --build`
- `docker exec osif_backend alembic upgrade head`
- `curl http://localhost:3000/api/v1/integrations`
- `curl http://localhost:3000/api/v1/ai/settings`
- Generate and download one report per format.
- Run one scan using a DB-backed integration key.

---

## Enterprise OSINT Notes

Phase 3.2 moves OSIF closer to enterprise readiness, but these items still matter after implementation:

- Add authentication and RBAC before multi-user production use.
- Add immutable audit logging for case edits, report downloads, integration changes, and AI analysis.
- Add credential rotation history.
- Add per-provider rate limit configuration.
- Add evidence snapshots for reports so report output does not silently change as graph data changes.
- Add redaction controls before sending case data to third-party AI providers.

---

## Phase 3.2 Definition of Done

- Case edit/status/severity workflows work from the UI.
- Reports support markdown, text, HTML, and PDF downloads.
- Integrations can be configured and tested from the UI.
- Integration secrets are stored encrypted in PostgreSQL.
- Existing `.env` integration keys still work during migration.
- AI settings can be configured and tested from the UI.
- AI secrets are stored encrypted in PostgreSQL.
- Backend does not return plaintext secrets.
- Docker migration and frontend build pass.
- `docs/phase3.2-plan.md` reflects the implemented design and any deviations.

---

## Recommended Plan Improvements

These improvements should be considered before implementation starts. They reduce delivery risk and make Phase 3.2 more suitable for enterprise OSINT use.

### 1. Split Phase 3.2 Into Smaller Milestones

Phase 3.2 is broad: case editing, reports, integrations, AI settings, secrets, and setup. Split it into smaller delivery slices:

- **Phase 3.2A:** Case edit workflow and HTML/PDF reports.
- **Phase 3.2B:** Encrypted settings and secrets foundation.
- **Phase 3.2C:** Integration migration, AI settings UI, and setup flow.

This keeps credential work isolated from lower-risk UI/report improvements.

### 2. Move Audit Logging Into Scope

Audit logging should not wait for a later enterprise phase because Phase 3.2 introduces case edits and credential changes.

Minimum model:

```text
audit_events
- id
- actor
- action
- resource_type
- resource_id
- case_id
- metadata
- ip_address
- user_agent
- created_at
```

Audit at minimum:

- case status, severity, assignment, and metadata edits
- report generation and downloads
- integration credential create/update/delete/test
- AI settings update/test
- AI analysis request metadata

Never log plaintext secrets or full AI prompts containing sensitive case data unless explicit retention controls are added.

### 3. Separate Priority From Severity

The current plan recommends keeping the DB field `priority` and labeling it as severity in the UI. That is a practical short-term shortcut, but enterprise OSINT benefits from separating:

- `priority`: operational urgency
- `severity`: risk or impact level

Recommended adjustment:

- Keep existing `cases.priority`.
- Add nullable `cases.severity` if implementation scope allows.
- Use the same value set initially: `critical`, `high`, `medium`, `low`.
- Update the UI to show both when `severity` exists.

If schema scope needs to stay small, keep the original plan for Phase 3.2 and add real `severity` in Phase 3.3.

### 4. Add Report Snapshots

Reports should represent what was known when the report was generated. They should not silently change when scans, notes, or graph data change later.

Add a JSON snapshot field:

```text
reports.snapshot
```

Store:

- case metadata
- scans and module statuses
- indicators
- relationships
- notes
- timeline entries
- generation timestamp

Render markdown, text, HTML, and PDF from the snapshot instead of live case data whenever possible.

### 5. Use One Secrets And Settings Foundation

Avoid building separate encryption paths for integrations and AI settings.

Create shared services:

- `SecretStore`
- `SettingsStore`
- `CredentialProvider`

Integrations and AI settings should both use these shared services. This keeps encryption, masking, validation, and rotation behavior consistent.

### 6. Add Encryption Key Versioning

Encrypted DB secrets need a future rotation path.

Add:

```text
key_version
```

to encrypted credential/settings records. Phase 3.2 can use a single `APP_ENCRYPTION_KEY`, but the schema should allow future key rotation without rewriting the model.

### 7. Gate Setup And Secrets Behind Admin Auth

Credential APIs are sensitive. If full auth/RBAC is not ready, use a temporary setup guard.

Recommended rule:

- Secret write/test/delete endpoints require admin auth.
- If admin auth is not available, require a one-time setup token from `.env`.

Example bootstrap value:

```text
SETUP_TOKEN=...
```

Read-only configured status can remain available to the UI, but secret mutation must be protected.

### 8. Define Credential Injection Clearly

OSINT modules should not query PostgreSQL directly or call `os.getenv(...)` after migration.

Preferred pattern:

```python
ExecutionContext(
    case_id=case_id,
    scan_id=scan_id,
    credentials=credential_provider,
)
```

The worker should preload credentials at scan start and pass an execution context into modules. This avoids async database calls deep inside module logic and keeps scan execution predictable.

### 9. Add Source Citations To Reports

Enterprise OSINT reports need defensible findings.

Each finding should preserve:

- source module
- scan ID
- timestamp
- confidence
- relationship type
- source/reference URL or raw evidence pointer when available

HTML and PDF reports should expose these citations in a compact way so an analyst can trace claims back to graph evidence.

### 10. Tighten The PDF Decision

Make the PDF path explicit before implementation:

- Default target: HTML template rendered to PDF.
- Preferred engine: Playwright/Chromium print-to-PDF if Docker can support it.
- Fallback engine: ReportLab plain PDF if Chromium is too heavy.

Do not block all Phase 3.2 work on perfect PDF styling. HTML should be implemented first, then PDF should render from the same report context.

### 11. Add Security Tests

Extend the testing plan with security-specific checks:

- plaintext secrets are never returned by APIs
- disabled credentials are not used by scans
- DB credentials override `.env`
- `.env` fallback logs safe metadata only
- audit event is created on credential update
- report downloads return non-empty bytes and correct MIME types
- invalid report IDs do not leak case/report metadata
- AI settings responses never expose API keys

### 12. Add A Rollback And Failure Plan

Add explicit failure behavior for migration-heavy work:

- downgrade test for new migrations
- fallback to `.env` if DB secret lookup fails
- controlled startup warning if `APP_ENCRYPTION_KEY` is missing
- fail closed for secret mutation endpoints when encryption is unavailable
- clear operator error when encrypted DB secrets cannot be decrypted

Phase 3.2 should fail safely: scans may use `.env` fallback during migration, but the app should never expose stored secrets or silently ignore decryption failures.

---

## Implementation Log

**Last updated:** 2026-07-02

### ✅ Step 1 — Case Edit UX (Done)

**Commits:** `15fd692`

- `CaseEditModal.vue` — full edit form: title, description, status, severity, case type, assigned analyst, client, jurisdiction, target name/aliases/location/DOB, tags, closed reason
- Inline status and severity quick-dropdowns in the `CaseDetail` header — change without opening modal
- Edit button on each case card in `CasesList.vue`
- `closed_reason` field added to `Case` model, `CaseUpdate` schema, `PATCH /status` endpoint
- Alembic migration: `a9166d45ecd7_add_closed_reason_to_cases.py`
- `form-label` utility class added to `style.css`

**Deviations from plan:**

- `PATCH /api/v1/cases/{case_id}/priority` was not added as a separate endpoint — quick priority changes go through the existing `PUT /{case_id}` via the store's `updateCase()`.
- Closed reason clears automatically when a case is reopened (handled in the PATCH status endpoint).

---

### ✅ Step 2 — Report Renderer (Done)

**Commits:** `e702888`, `4bbda6b`, `8ecb8ca`, `d43e32f`

- `backend/app/services/report_renderer.py` — new service with:
  - `build_snapshot()` — captures point-in-time JSON of case, scans, indicators, edges, notes
  - `render_html()` — self-contained HTML report from snapshot (inline CSS, no external deps)
  - `render_pdf()` — structured PDF via `reportlab` (pure Python, tables for indicators/relationships)
  - `render_markdown_to_html()` — wraps existing markdown content in an HTML page for preview
- `GET /api/v1/reports/{id}/download` — serves correct Content-Type + filename per format
- `GET /api/v1/reports/{id}/preview` — renders HTML in browser tab
- `snapshot` JSONB column added to `reports` table — reports are frozen at generation time
- Frontend: HTML and PDF format options added to the Generate Report form
- Frontend: Preview button on HTML/PDF report cards
- Frontend: Download uses `fetch()` → blob → object URL — page no longer navigates away on download
- Alembic migration: `77b230d431b5_add_snapshot_to_reports.py`

**Bugs fixed during implementation:**

| Bug | Cause | Fix |
|-----|-------|-----|
| `AttributeError: 'Indicator' has no 'source_module'` | `Indicator` model stores source in `meta` JSONB, not a column | Read `i.meta.get("source_module", "")` |
| Download saved as `download.html` and navigated away | `a.download = ''` uses URL path segment as filename | `fetch()` as blob, set `a.download = filename` explicitly |
| PDF opened as "Failed to load PDF document" | `xhtml2pdf` crashes with SIGILL (AVX instructions not supported by Docker host CPU) | Replaced with pure `reportlab` renderer — no C extensions |

**Deviations from plan:**

- PDF is generated directly from the snapshot via `reportlab` (not HTML-to-PDF). Output is structured and clean but not pixel-perfect HTML styling. HTML-to-PDF (Playwright) remains a Phase 3.3 option.
- `xhtml2pdf` removed from `requirements.txt` entirely — `reportlab` was already a transitive dependency and works correctly on this CPU.

---

### ⏳ Step 3 — Secrets Foundation (Pending)

- `backend/app/core/crypto.py` — Fernet encryption using `APP_ENCRYPTION_KEY`
- `IntegrationCredential` model + schema + migration
- `backend/app/services/credentials.py` — DB-first lookup with `.env` fallback, Redis TTL cache
- Integration CRUD + test endpoints (`PUT`, `POST /test`, `DELETE`, `POST /import-env`)
- Update `IntegrationsView.vue` — save/test credentials, masked display

---

### ⏳ Step 4 — Migrate OSINT Modules (Pending, depends on Step 3)

- Worker loads credentials at scan start and passes them into module execution context
- Modules to migrate: Shodan, VirusTotal, AbuseIPDB, Tomba, URLScan
- Modules stop calling `os.getenv()` directly

---

### ⏳ Step 5 — AI Settings (Pending, depends on Step 3)

- `AISetting` model + schema + migration
- `GET/PUT /api/v1/ai/settings` — read/write DB-backed AI config
- `POST /api/v1/ai/test` — test active provider
- Update `AiSettingsView.vue` — provider selector, model, key input, base URL (Ollama), test button

---

### ⏳ Step 6 — Setup Experience (Pending, depends on Steps 3–5)

- First-run setup route or admin settings area
- `.env` import action (`POST /api/v1/integrations/import-env`)
- "Configured from DB" vs "Using environment fallback" status indicators
