<div align="center">

# OSIF v2.0 — Open Source Intelligence Framework

[![License](https://img.shields.io/badge/license-AGPL%20v3-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

**Enterprise-grade OSINT platform with graph-based investigation workspace, real-time scan engine, and Maltego-style visualization.**

[Quick Start](#quick-start) • [Architecture](#architecture) • [Configuration](#configuration) • [API](#api-reference) • [Development](#development)

</div>

---

## Overview

OSIF v2.0 is a complete rewrite of the original CLI tool into a full-stack, API-first investigation platform. It is designed for security researchers, penetration testers, and PI/skip-tracing workflows.

**What's new in v2:**

- FastAPI async backend replacing the Flask CLI
- PostgreSQL + SQLAlchemy 2.0 for persistent case and graph storage
- arq + Redis task queue for parallel async scan execution
- Vue 3 frontend with Cytoscape.js graph visualization
- MinIO S3-compatible object storage for evidence files
- Case knowledge graph — manual entities, relationships, provenance tracking
- 11+ OSINT modules with caching, rate limiting, and auto-correlation

---

## Screenshots

### Investigation Graph

![Graph](screenshots/v2/graph.png "Case knowledge graph with manual entities and scan indicators")

### Scan Execution

![Scan](screenshots/v2/scan.png "Real-time scan progress with module status")

### Timeline

![Timeline](screenshots/v2/timeline.png "Case timeline with events and evidence")

### Integrations

![Integrations](screenshots/v2/integration.png "API key management and integration settings")

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Stack                     │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐  ┌─────────┐ │
│  │ frontend │   │ backend  │   │  worker  │  │ console │ │
│  │ Vue 3    │   │ FastAPI  │   │   arq    │  │  CLI    │ │
│  │ :3000    │   │ :6000    │   │          │  │         │ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘  └────┬────┘ │
│       │              │               │              │       │
│  ┌────▼──────────────▼───────────────▼──────────────▼────┐ │
│  │                    Internal Network                    │ │
│  └────┬──────────────────────────┬───────────────────────┘ │
│       │                          │                          │
│  ┌────▼─────┐  ┌─────────┐  ┌───▼──────┐                  │
│  │ postgres │  │  redis  │  │  minio   │                  │
│  │ :5434    │  │  :6381  │  │  :9100   │                  │
│  └──────────┘  └─────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Services

| Service      | Image                  | Port (host) | Purpose                                 |
|--------------|------------------------|-------------|-----------------------------------------|
| `frontend`   | Custom (Nginx + Vue)   | 3000        | Web UI — investigation dashboard        |
| `backend`    | Custom (FastAPI)       | 6000        | REST API + WebSocket                    |
| `worker`     | Custom (arq)           | —           | Async scan task execution               |
| `console`    | Custom (CLI)           | —           | Metasploit-style REPL (`./osif`)        |
| `postgres`   | postgres:16-alpine     | 5434        | Primary database (cases, graph, scans)  |
| `redis`      | redis:7-alpine         | 6381        | Task queue + caching + rate limiting    |
| `minio`      | minio/minio:latest     | 9100 / 9101 | Evidence file storage (S3-compatible)   |
| `minio-init` | minio/mc:latest        | —           | One-shot bucket provisioning            |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2 (bundled with Docker Desktop)

### 1. Clone the repository

```bash
git clone https://github.com/fr4nc1stein/osint-framework osif
cd osif
git checkout feature/v2
```

### 2. Configure environment

```bash
cp backend/.env.example .env
```

Edit `.env` and add any API keys you have (all are optional — free-tier modules work without keys):

```env
# OSINT API Keys (optional)
SHODAN_API_KEY=
VT_API=
ABUSEIPDB_API_KEY=
TOMBA_API_KEY=
TOMBA_SECRET_KEY=
HUNTER_API_KEY=
```

### 3. Start all services

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

The backend entrypoint automatically:
- Waits for PostgreSQL and Redis to be healthy
- Runs all Alembic migrations (`alembic upgrade head`)
- Provisions the MinIO `osif-evidence` bucket
- Starts the FastAPI server on port 6000

### 4. Verify everything is running

```bash
docker-compose -f docker-compose.dev.yml ps
```

Expected output:

```
NAME                STATUS              PORTS
osif_postgres       Up (healthy)        0.0.0.0:5434->5432/tcp
osif_redis          Up (healthy)        0.0.0.0:6381->6379/tcp
osif_minio          Up (healthy)        0.0.0.0:9100->9000/tcp, 0.0.0.0:9101->9001/tcp
osif_minio_init     Exited (0)
osif_backend        Up                  0.0.0.0:6000->6000/tcp
osif_worker         Up
osif_frontend       Up                  0.0.0.0:3000->80/tcp
osif_console        Up
```

### 5. Open the UI

| Interface              | URL                        |
|------------------------|----------------------------|
| Investigation Dashboard | http://localhost:3000      |
| API (Swagger docs)     | http://localhost:6000/api/docs |
| MinIO Console          | http://localhost:9101      |

---

## Database Tables

Migrations run automatically on startup. Current schema (Phase 3.4):

```
cases               — Investigation containers
scans               — OSINT scan jobs
indicators          — Graph nodes (discovered data)
edges               — Graph edges (discovered relationships)
scan_findings       — Scan ↔ edge association
scan_templates      — Reusable module presets
case_entities       — Manual graph nodes (PI workspace)
case_relationships  — Manual graph edges
case_evidence       — Evidence file attachments
case_evidence_links — Evidence ↔ node association
alembic_version     — Migration state
```

---

## OSINT Modules

11 modules ship out of the box. All modules run in parallel via the arq worker.

| # | Module ID           | Category | API Key | Cache | Rate Limit  |
|---|---------------------|----------|---------|-------|-------------|
| 1 | `dns_records`       | domain   | —       | ✅    | —           |
| 2 | `subdomain_enum`    | domain   | —       | ✅    | —           |
| 3 | `whois_lookup`      | domain   | —       | ✅    | —           |
| 4 | `email_hunter`      | domain   | ✅      | ✅    | tomba       |
| 5 | `virustotal_domain` | domain   | ✅      | ✅    | 4 req/min   |
| 6 | `urlscan_lookup`    | domain   | —       | ✅    | 1 req/2s    |
| 7 | `ip_geolocation`    | ip       | —       | ✅    | —           |
| 8 | `abuseipdb`         | ip       | ✅      | ✅    | 1000/day    |
| 9 | `shodan_lookup`     | ip       | ✅      | ✅    | 1 req/s     |
| 10 | `email_domain`     | email    | —       | ✅    | —           |
| 11 | `hibp_breach`      | email    | —       | ✅    | —           |

---

## Configuration

### Environment Variables

All configuration is managed via `.env` at the project root. The file is loaded by both `backend` and `worker` services via `env_file`.

```env
# Application
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://osif:osif@postgres:5432/osif
DATABASE_POOL_SIZE=20

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_POOL_SIZE=10

# API Server
API_PORT=6000
API_WORKERS=4
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Worker
WORKER_CONCURRENCY=4
REQUEST_DELAY_MS=500

# Evidence Storage (MinIO / S3-compatible)
EVIDENCE_STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=osif-evidence
S3_ACCESS_KEY=osif_minio
S3_SECRET_KEY=osif_minio_password
S3_REGION=us-east-1
S3_FORCE_PATH_STYLE=true

# Security
SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# OSINT API Keys
VT_API=
SHODAN_API_KEY=
ABUSEIPDB_API_KEY=
HUNTER_API_KEY=
TOMBA_API_KEY=
TOMBA_SECRET_KEY=
```

> **For production:** Change `SECRET_KEY`, `MINIO_ROOT_PASSWORD`, and the database password. Set `DEBUG=false`.

### MinIO Credentials

Default MinIO credentials (change for production):

| Setting        | Default              |
|----------------|----------------------|
| Root user      | `osif_minio`         |
| Root password  | `osif_minio_password` |
| Bucket         | `osif-evidence`      |
| Console URL    | http://localhost:9101 |

---

## API Reference

Base URL: `http://localhost:6000`

### Health

```
GET  /health        — Liveness probe
GET  /ready         — Readiness probe (DB + Redis)
```

### Cases

```
POST   /api/v1/cases                   — Create case
GET    /api/v1/cases                   — List cases
GET    /api/v1/cases/{id}              — Get case
PUT    /api/v1/cases/{id}              — Update case
DELETE /api/v1/cases/{id}              — Delete case
```

### Scans

```
POST   /api/v1/scans                   — Launch scan (enqueues to arq)
GET    /api/v1/scans                   — List scans
GET    /api/v1/scans/{id}              — Get scan + progress
GET    /api/v1/scans/{id}/graph        — Get scan graph (nodes + edges)
```

### Case Graph (PI Workspace)

```
GET    /api/v1/cases/{id}/graph        — Merged case knowledge graph
GET    /api/v1/cases/{id}/scans        — Case scan list
GET    /api/v1/cases/{id}/entities     — List manual entities
POST   /api/v1/cases/{id}/entities     — Create manual entity
PUT    /api/v1/cases/{id}/entities/{eid} — Update entity
DELETE /api/v1/cases/{id}/entities/{eid} — Delete entity
GET    /api/v1/cases/{id}/relationships — List manual relationships
POST   /api/v1/cases/{id}/relationships — Create relationship
PUT    /api/v1/cases/{id}/relationships/{rid} — Update relationship
DELETE /api/v1/cases/{id}/relationships/{rid} — Delete relationship
```

### Evidence

```
GET    /api/v1/cases/{id}/evidence     — List evidence
POST   /api/v1/cases/{id}/evidence     — Link URL/note as evidence
POST   /api/v1/cases/{id}/evidence/upload — Upload file (stored in MinIO)
DELETE /api/v1/cases/{id}/evidence/{eid}  — Delete evidence
```

### Modules & Templates

```
GET    /api/v1/modules                 — List all OSINT modules
GET    /api/v1/modules/{id}            — Get module details
POST   /api/v1/templates               — Create scan template
GET    /api/v1/templates               — List templates
GET    /api/v1/templates/{id}          — Get template
DELETE /api/v1/templates/{id}          — Delete template
```

### Export

```
GET    /api/v1/export/{scan_id}/json   — Export scan as JSON
GET    /api/v1/export/{scan_id}/csv    — Export as CSV (edges or nodes)
GET    /api/v1/export/{scan_id}/graphml — Export as GraphML (Gephi/Cytoscape)
```

### WebSocket

```
WS     /ws/scan/{scan_id}             — Real-time scan events
```

Event types: `module_start`, `discovery`, `module_complete`, `module_error`, `scan_complete`, `auto_linker_complete`

**Interactive docs:** http://localhost:6000/api/docs

---

## Scan Execution Flow

```
POST /api/v1/scans
        ↓
   Tasks enqueued (one arq job per module)
        ↓
   For each module (parallel):
     1. Check rate limit (Redis)
     2. Check result cache (Redis)
     3. Execute module against target
     4. Cache results
     5. Build graph (upsert indicators + edges)
     6. Publish WebSocket events
        ↓
   All modules complete
        ↓
   Auto-linker runs:
     - Finds corroborations (same relationship from 2+ modules)
     - Infers transitive relationships
     - Publishes correlation stats
        ↓
   Scan status → completed
```

---

## CLI Console

The `console` service gives you the original Metasploit-style REPL, now API-connected:

```bash
docker exec -it osif_console ./osif
```

```
─$ ./osif


                                                         ##     ####   #####   ######
                                                        #  #   #    #    #     #
                                                       #    #  #         #     #
                                                       #    #   ####     #     ####
                                                       #    #       #    #     #
                                                        #  #   #    #    #     #
                                                         ##     ####   #####   #


                                                             >> OSINT Framework
                                                                 >> @laet4x



        -=[ 1 api           ]=-
        -=[ 2 dns           ]=-
        -=[ 1 subdomain     ]=-
        -=[ 1 uncategorized ]=-

[!] There are some issues ; use 'show issues' to see more details
osif > use dns/dns_records
osif dns(dns_records) > show options

Module options
==============

   Name    Value       Required  Description
   ----    -----       --------  -----------
   DOMAIN  google.com  Y         Provide your target Domain

osif dns(dns_records) >
```

### Shodan Attack Surface

![Shodan](screenshots/attack_surface_shodan.png "Attack Surface")

### Email Hunter (Hunter.io & Tomba)

![Email Hunter](screenshots/email_hunter.png "Hunting Domain Email")

### GeoWifi Hunter

![GeoWifi Hunter](screenshots/geo_wifi.png "Hunting Geolocation of WiFi SSID")

### Web Graph (v1)

![Web Graph](screenshots/web_graph.png "Graph Visualization")

---

## Development

### Local backend + frontend dev server

```bash
# Start infrastructure only
docker-compose -f docker-compose.dev.yml up -d postgres redis minio minio-init

# Run backend with hot reload
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 6000

# Run arq worker
arq app.tasks.worker.WorkerSettings

# Run frontend dev server (in a separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Rebuild after code changes

```bash
# Rebuild and restart all services
docker-compose -f docker-compose.dev.yml up -d --build

# Or restart a single service
docker-compose -f docker-compose.dev.yml up -d --build backend
```

### View logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific services
docker-compose -f docker-compose.dev.yml logs -f backend worker
```

### Database access

```bash
docker-compose -f docker-compose.dev.yml exec postgres psql -U osif
```

### Run a new migration

```bash
# From inside the backend container
docker-compose -f docker-compose.dev.yml exec backend \
  alembic revision --autogenerate -m "describe your change"

# Apply
docker-compose -f docker-compose.dev.yml exec backend \
  alembic upgrade head
```

### Stop and clean up

```bash
# Stop all services (keep volumes)
docker-compose -f docker-compose.dev.yml down

# Stop and remove all data volumes
docker-compose -f docker-compose.dev.yml down -v
```

---

## What's Complete

| Phase | Feature Area                        | Status |
|-------|-------------------------------------|--------|
| 1     | FastAPI backend, PostgreSQL, 6 modules, Docker | ✅ |
| 2     | arq task queue, WebSocket, graph service, 8 modules | ✅ |
| 3     | Auto-linker, Redis caching, rate limiting, 11 modules, scan templates, export | ✅ |
| 3.1   | Case management UI, case-scoped graph | ✅ |
| 3.2   | Encrypted integration credentials, AI settings, first-run setup | ✅ |
| 3.3   | Timeline, notes, reports | ✅ |
| 3.4-A | Manual entities and relationships (PI workspace) | ✅ |
| 3.4-B | Evidence attachments (MinIO file storage) | ✅ |

---

## Troubleshooting

### Services not starting

```bash
# Check health status
docker-compose -f docker-compose.dev.yml ps

# Check startup logs
docker-compose -f docker-compose.dev.yml logs backend
docker-compose -f docker-compose.dev.yml logs minio
```

### Database migration errors

```bash
# Check current migration state
docker-compose -f docker-compose.dev.yml exec backend alembic current

# Apply pending migrations manually
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

### MinIO bucket not created

```bash
# Re-run the init container
docker-compose -f docker-compose.dev.yml run --rm minio-init
```

### Port conflicts

Default host ports used:

| Port | Service           |
|------|-------------------|
| 3000 | Frontend (Nginx)  |
| 5434 | PostgreSQL        |
| 6000 | Backend API       |
| 6381 | Redis             |
| 9100 | MinIO API         |
| 9101 | MinIO Console     |

Change host-side ports in `docker-compose.dev.yml` if any conflict with existing services.

### Module not discovered

```bash
# List all discovered modules
curl http://localhost:6000/api/v1/modules | jq '[.[] | .module_id]'

# Check backend logs for import errors
docker-compose -f docker-compose.dev.yml logs backend | grep -i "module\|error"
```

---

## License

AGPL v3 — see [LICENSE.md](LICENSE.md)

---

*OSIF v2.0 — Branch `feature/v2`*
