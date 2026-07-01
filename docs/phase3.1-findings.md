# OSIF v2.0 - Phase 3.1 Findings

**Date:** 2026-07-01  
**Scope:** Review of all `docs/*.md`, with focus on `docs/phase3.1-plan.md` and current backend/frontend implementation.

---

## Summary

Phase 3.1 is partially implemented already. The codebase includes case-centric views, reports, notes, unified case graphs, integrations, AI settings, theme support, `parent_scan_id`, and scan children APIs.

The main readiness gaps are not around feature count. They are around correctness, operational resilience, auditability, security, and test coverage. For enterprise OSINT use, the platform needs stronger evidence handling, per-module execution tracking, RBAC, audit logs, legal/ethical controls, and automated tests.

## Remediation Status

Items addressed after this findings document was created:

- Fixed the SQLAlchemy 2 readiness probe issue by wrapping `SELECT 1` in `text()`.
- Added `PATCH /api/v1/cases/{case_id}/status`.
- Added module-level scan status tracking via `Scan.module_statuses`.
- Added resilient scan finalization with `completed`, `partial`, and `failed` outcomes.
- Preserved module error WebSocket events without immediately failing the entire scan.
- Added migration coverage for `module_statuses`.
- Named the Phase 3.1 `parent_scan_id` foreign key constraint.
- Reworked `/api/v1/modules/suggest` to derive suggestions from module `ACCEPTS` metadata.
- Removed the unused duplicate module suggestion router in `scan_children.py`.
- Fixed case graph node scan launches to pass `parent_scan_id` when the parent scan can be resolved unambiguously.
- Added module suggestions to the case graph-node scan modal.
- Added frontend handling for `partial` and `failed` scan states.
- Added `url` as a supported scan seed kind for URL-capable modules.
- Added `frontend/.nvmrc` with Node `20.19.0`.

Remaining high-priority gaps:

- Add authentication and RBAC.
- Add immutable audit logging.
- Add automated backend, frontend, migration, and worker tests.
- Add true worker job cancellation for deleted/cancelled scans.
- Add evidence governance and chain-of-custody hardening.
- Add CI that runs backend compile/tests, migrations, and frontend build with Node 20+.

---

## Implemented Phase 3.1 Items

The following Phase 3.1 items appear to exist in the current source:

- Case list and case detail frontend views.
- Case tabs for scans, graph, timeline, notes, and reports.
- Case notes model, schema, API, and UI.
- Reports model, schema, API, and UI.
- Unified case graph endpoint at `GET /api/v1/cases/{case_id}/graph`.
- Case scans endpoint at `GET /api/v1/cases/{case_id}/scans`.
- `parent_scan_id` field on `Scan`.
- Scan children endpoint at `GET /api/v1/scans/{scan_id}/children`.
- Module suggestion endpoint at `GET /api/v1/modules/suggest`.
- Integrations catalog endpoint and frontend view.
- AI settings and AI analyst endpoints/views.
- Theme store and theme initialization.

---

## Confirmed Bugs And Risks

### 1. Readiness Probe May Fail With SQLAlchemy 2

**File:** `backend/app/main.py`  
**Line:** readiness endpoint database check

The code uses:

```python
await db.execute("SELECT 1")
```

With SQLAlchemy 2, raw SQL should be wrapped in `text()`:

```python
from sqlalchemy import text
await db.execute(text("SELECT 1"))
```

**Impact:** `/ready` may return `not_ready` even when PostgreSQL is healthy.

**Priority:** High

---

### 2. Scan From Graph Node Does Not Preserve Parent Scan

**File:** `frontend/src/views/CaseDetail.vue`  
**Area:** second `CreateScanModal` for graph-node scans

The UI opens a scan modal from a graph node, but it does not pass `parentScanId`. That means derived scans are created in the case, but not linked into the parent/child hierarchy.

**Impact:** hierarchical investigation workflows lose lineage.

**Priority:** High

**Recommended fix:** determine the source scan for the selected node or edge and pass it into:

```vue
<CreateScanModal
  :parent-scan-id="..."
/>
```

If a node exists in multiple scans, the UI should ask the analyst which scan should be the parent, or default to the current selected scan origin.

---

### 3. One Module Failure Marks Entire Scan As Error

**File:** `backend/app/tasks/scan_tasks.py`  
**Area:** exception handling in `run_scan_task`

The worker marks the entire scan as `error` when one module fails.

**Impact:** OSINT scans are brittle. External APIs frequently rate-limit, timeout, or return incomplete results. A single failed module should not invalidate all successful findings.

**Priority:** High

**Recommended fix:**

- Add per-module execution records.
- Track module states: `queued`, `running`, `completed`, `failed`, `skipped`, `rate_limited`.
- Allow scan-level statuses such as `completed`, `partial`, `failed`, and `cancelled`.
- Mark scan as `partial` when at least one module succeeds and at least one fails.

---

### 4. Empty Alembic Migrations Remain In The Chain

**Files:**

- `backend/alembic/versions/ee1aa765cff4_add_scan_templates_table_for_phase_3.py`
- `backend/alembic/versions/2728f52b547e_add_scan_templates_table.py`
- `backend/alembic/versions/4618a5e43fd7_add_scan_templates_table_phase_3.py`

These migrations contain only `pass`.

**Impact:** They may not break upgrades, but they create operational confusion and contradict the Phase 3.1 migration guardrails.

**Priority:** Medium

**Recommended fix:** clean up migration history before production use. If this branch has not been deployed, squash or rewrite the empty migrations. If it has been deployed, leave them but document why they exist and avoid adding more empty revisions.

---

### 5. Phase 3.1 Migration Uses Unnamed Foreign Key

**File:** `backend/alembic/versions/b6eef2208ca7_phase3_1_schema.py`

The migration creates and drops an unnamed FK:

```python
op.create_foreign_key(None, 'scans', 'scans', ['parent_scan_id'], ['id'], ondelete='SET NULL')
op.drop_constraint(None, 'scans', type_='foreignkey')
```

**Impact:** Downgrades can be fragile because the database generates the constraint name.

**Priority:** Medium

**Recommended fix:** name the constraint explicitly, for example:

```python
op.create_foreign_key(
    "fk_scans_parent_scan_id_scans",
    "scans",
    "scans",
    ["parent_scan_id"],
    ["id"],
    ondelete="SET NULL",
)
```

---

### 6. No Automated Tests Found

No backend or frontend test files were found.

**Impact:** Enterprise readiness cannot be validated. Regression risk is high across migrations, scan execution, graph merging, and frontend workflows.

**Priority:** High

**Recommended first tests:**

- Backend unit tests for module registry and module suggestions.
- Backend API tests for cases, scans, reports, notes, and case graph.
- Worker tests for successful, failed, partial, cached, and rate-limited module runs.
- Migration test from empty database to head.
- Frontend component tests for `CreateScanModal`, `CaseDetail`, and graph-node scan flow.
- E2E test for creating a case, launching a scan, viewing graph data, generating a report, and exporting results.

---

### 7. Local Frontend Build Blocked By Node Version

The local machine has Node `16.14.2`. Current Vite requires Node `20.19+` or `22.12+`.

**Impact:** Frontend build verification cannot run locally with the current Node version.

**Priority:** Medium

**Recommended fix:** standardize runtime versions with one of:

- `.nvmrc`
- `.node-version`
- Volta config in `package.json`
- documented Docker-only build path

---

## Enterprise OSINT Improvements

### Security And Access Control

- Add authentication.
- Add RBAC roles: admin, analyst, viewer, auditor.
- Add case-level and tenant-level access control.
- Add API tokens for CLI and external integrations.
- Encrypt API keys at rest instead of only reading from environment variables.
- Add secret rotation support.
- Add session expiration and refresh flow.
- Enforce HTTPS in production.

### Auditability

- Add immutable audit logs for:
  - case creation and updates
  - scan launches and cancellations
  - module execution
  - notes and report changes
  - evidence uploads
  - exports
  - API key checks
  - AI analysis requests
- Include actor, timestamp, IP address, user agent, object ID, and before/after changes.

### Evidence And Chain Of Custody

- Store source URL, collection time, collector, hash, and acquisition method for every evidence item.
- Add immutable chain-of-custody events.
- Add evidence versioning.
- Add evidence integrity verification.
- Add analyst attestations for final reports.

### Legal And Ethical Controls

- Add per-case authorization metadata:
  - client
  - jurisdiction
  - authorization scope
  - allowed collection methods
  - expiration date
- Label modules by collection risk:
  - passive
  - semi-active
  - active
  - intrusive
- Require explicit confirmation before active or intrusive modules.
- Track source terms and usage restrictions for external APIs.

### Operational Resilience

- Add per-module execution records.
- Add retries with backoff for transient provider failures.
- Add timeout policies per module.
- Add scan cancellation that actually cancels queued/running worker jobs.
- Add dead-letter handling for failed jobs.
- Add provider quota dashboards.
- Add cache observability: hit rate, miss rate, TTL, invalidation.

### Data Quality

- Add normalized indicator values and raw observed values separately.
- Add confidence provenance, not just confidence score.
- Add source reliability scoring.
- Add analyst-reviewed entity merging.
- Add false-positive marking.
- Add stale-data marking and revalidation workflows.

### Reporting And Export

- Add PDF reports.
- Add report templates by audience:
  - executive
  - technical
  - legal
  - timeline
  - evidence appendix
- Add STIX 2.1 export.
- Add MISP-compatible export.
- Add report snapshots so generated reports do not silently change as graph data changes.

---

## Feature Suggestions

### Case Workflow

- Make Cases the primary landing page for analysts.
- Add case dashboard widgets:
  - open cases
  - overdue cases
  - recent findings
  - high-risk indicators
  - failed modules
- Add case assignment and review status.
- Add case templates for common investigation types.

### Graph Workflow

- Add filters by:
  - scan
  - module
  - indicator kind
  - confidence
  - source
  - time discovered
- Add graph legends for scan origin and module origin.
- Add node clustering by organization, ASN, domain, or source scan.
- Add analyst annotations on nodes and edges.
- Add “hide low confidence” and “show only high-risk” controls.
- Add graph snapshots for reports.

### Scan Workflow

- Add playbooks beyond scan templates.
- Add scheduled re-scans.
- Add watchlists for domains, IPs, emails, usernames, and crypto addresses.
- Add scan diffing: what changed since the last scan.
- Add module compatibility validation before launching a scan.
- Add clear API-key warnings before selecting modules that cannot run.

### AI Analyst

- Send richer context to the AI endpoint:
  - case details
  - scans
  - graph nodes and edges
  - notes
  - reports
  - module errors
- Add cited AI output so every claim references graph evidence.
- Add prompt templates:
  - summarize findings
  - identify next steps
  - draft executive report
  - find weak links
  - explain confidence gaps
- Add redaction controls before sending case data to third-party LLMs.

### Integrations

- Add test connection endpoints.
- Add last successful check timestamp.
- Add quota remaining where providers support it.
- Add per-integration health status.
- Add provider-specific setup instructions.

---

## Recommended Bug-Fix Backlog

### P0

- Add authentication/RBAC before any production or shared deployment.
- Add audit logging for case, scan, report, note, export, and evidence events.
- Add automated migration verification from empty database to head.

### P1

- Fix `/ready` SQLAlchemy raw SQL issue.
- Preserve `parent_scan_id` when launching scans from graph nodes.
- Replace scan-level hard failure with per-module status and partial scan completion.
- Add backend API tests for Phase 3.1 endpoints.
- Add frontend build/runtime version enforcement.

### P2

- Clean or document empty Alembic migrations.
- Name the `parent_scan_id` FK constraint.
- Remove duplicate module suggestion mapping logic and derive suggestions from module `ACCEPTS`.
- Add scan cancellation support.
- Add provider quota and rate-limit visibility.

### P3

- Add STIX/MISP exports.
- Add report snapshots.
- Add graph snapshots.
- Add scheduled scans and scan diffs.
- Add AI citations and redaction controls.

---

## Verification Performed

Backend syntax verification passed with:

```bash
python3 -m compileall -q backend/app
```

Frontend build verification was attempted with:

```bash
npm run build
```

It failed because the local Node version is `16.14.2`, while Vite requires Node `20.19+` or `22.12+`.

---

## Overall Readiness Assessment

OSIF v2.0 is moving from a scan-centric tool toward a case-centric investigation platform, and Phase 3.1 is directionally correct.

It is not enterprise-ready yet. The blockers are:

- no authentication/RBAC
- no audit logging
- no automated tests
- brittle scan error handling
- limited evidence governance
- incomplete operational controls
- incomplete migration hygiene

Once those are addressed, the platform will be much closer to an enterprise OSINT system rather than a useful investigation prototype.
