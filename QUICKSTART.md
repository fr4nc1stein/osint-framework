# OSIF v2.0 — Quick Start

## One-Command Setup

```bash
git clone https://github.com/fr4nc1stein/osint-framework osif
cd osif
git checkout feature/v2
cp backend/.env.example .env
docker-compose -f docker-compose.dev.yml up -d --build
```

The stack starts automatically:
- Waits for PostgreSQL and Redis to be healthy
- Provisions the MinIO `osif-evidence` bucket
- Runs all Alembic migrations
- Starts backend API on port 6000
- Serves the frontend on port 3000

## Verify All Services

```bash
docker-compose -f docker-compose.dev.yml ps
```

```
NAME              STATUS         PORTS
osif_postgres     Up (healthy)   0.0.0.0:5434->5432/tcp
osif_redis        Up (healthy)   0.0.0.0:6381->6379/tcp
osif_minio        Up (healthy)   0.0.0.0:9100->9000/tcp, 0.0.0.0:9101->9001/tcp
osif_minio_init   Exited (0)
osif_backend      Up             0.0.0.0:6000->6000/tcp
osif_worker       Up
osif_frontend     Up             0.0.0.0:3000->80/tcp
osif_console      Up
```

## Open the UI

| Interface | URL |
|---|---|
| Investigation Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:6000/api/docs |
| MinIO Console | http://localhost:9101 |

## Case Workspace Tabs

Once you open a case at http://localhost:3000/cases, you get:

| Tab | What it does |
|---|---|
| **Graph** | Interactive Cytoscape.js knowledge graph — scan indicators + manual entities + relationships |
| **Timeline** | Chronological event log linked to entities, evidence, and scans |
| **Evidence** | File upload library backed by MinIO — attach screenshots, PDFs, images to any node |
| **Leads** | Review queue for scan-derived findings — promote, reject, or merge into confirmed entities |
| **Map** | Location markers for address/location entities, IP geolocation results, and sightings |
| **Dossier** | Subject intelligence briefing — confirmed entities, relationships, locations, open leads |
| **Scans** | Hierarchical scan list — parent/child relationships, provenance badges |
| **Notes** | Investigation notes |
| **Reports** | Generate and download Markdown, HTML, or PDF reports including PI dossier format |

## Quick API Test

```bash
# Health check
curl http://localhost:6000/health

# List OSINT modules
curl http://localhost:6000/api/v1/modules | jq '[.[] | .module_id]'

# Create a case
curl -X POST http://localhost:6000/api/v1/cases \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Investigation", "description": "Testing OSIF v2.0", "priority": "high"}'

# Launch a scan
curl -X POST http://localhost:6000/api/v1/scans \
  -H "Content-Type: application/json" \
  -d '{"seed_value": "example.com", "seed_kind": "domain", "modules": ["dns_records", "whois_lookup"]}'
```

## CLI Console

```bash
docker exec -it osif_console ./osif
```

## View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Backend + worker only
docker-compose -f docker-compose.dev.yml logs -f backend worker
```

## Stop

```bash
# Keep data volumes
docker-compose -f docker-compose.dev.yml down

# Wipe everything (fresh start)
docker-compose -f docker-compose.dev.yml down -v
```

## Rebuild After Changes

```bash
docker-compose -f docker-compose.dev.yml up -d --build

# Single service
docker-compose -f docker-compose.dev.yml up -d --build backend
```

## Troubleshooting

**Port already in use:**
```bash
lsof -i :6000   # or :3000, :5434, :6381, :9100
```
Change host-side ports in `docker-compose.dev.yml` to resolve conflicts.

**Database not ready:**
```bash
docker-compose -f docker-compose.dev.yml logs postgres
docker-compose -f docker-compose.dev.yml exec postgres psql -U osif -c "\dt"
```

**Run migration manually:**
```bash
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

**Reset MinIO bucket:**
```bash
docker-compose -f docker-compose.dev.yml run --rm minio-init
```

---

**Backend API:** http://localhost:6000  
**Frontend:** http://localhost:3000  
**Docs:** http://localhost:6000/api/docs
