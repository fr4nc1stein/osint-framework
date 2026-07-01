# OSIF v2.0 — Technical Specification

**Project:** Open Source Intelligence Framework v2.0  
**Chief Architect:** System Design Document  
**Date:** 2026-06-30  
**Status:** Planning Phase

---

## 📋 Executive Summary

OSIF v2.0 represents a complete architectural evolution from the current monolithic Flask application to a modern, scalable OSINT platform with:

- **Separated Frontend**: Vue 3 + TypeScript (based on IdentiAi UI)
- **Backend API**: FastAPI with async/await (replacing Flask)
- **Database**: PostgreSQL 16 for persistence (replacing in-memory storage)
- **Task Queue**: Redis + arq for async OSINT operations
- **CLI**: Retained Metasploit-style interface with enhanced API integration

**Migration Strategy**: Incremental — CLI remains functional while new stack is built alongside.

---

## 🎯 Project Goals

### Primary Objectives

1. **Retire Static Templates** — Replace Flask templates/static files with dedicated Vue.js SPA
2. **Add Persistence** — PostgreSQL for investigations, cases, and graph data
3. **Async Operations** — Non-blocking OSINT module execution
4. **Case Management** — Full investigation lifecycle (from IdentiAi)
5. **Modern UI** — Dark tactical interface with graph visualization
6. **API-First** — RESTful backend that CLI and frontend both consume

### Success Criteria

- [ ] Frontend runs independently on port 5173 (Vite dev server)
- [ ] Backend API on port 8000 (FastAPI)
- [ ] CLI can trigger scans via API (backward compatible)
- [ ] Graph data persists across restarts
- [ ] Case management with full CRUD operations
- [ ] WebSocket live feed for real-time updates

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          OSIF v2.0 Platform                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐         ┌──────────────────────────────────┐ │
│  │   CLI Interface  │         │   Vue 3 Frontend (SPA)           │ │
│  │   (osif script)  │         │   Port: 5173 (dev) / 3000 (prod)│ │
│  │                  │         │                                  │ │
│  │  • Metasploit    │         │  • Dark tactical UI              │ │
│  │    commands      │         │  • Cytoscape graph               │ │
│  │  • Module mgmt   │         │  • Case management               │ │
│  │  • API client    │         │  • Live feed (WebSocket)         │ │
│  └────────┬─────────┘         │  • Evidence tracking             │ │
│           │                   └──────────────┬───────────────────┘ │
│           │                                  │                     │
│           └──────────┬───────────────────────┘                     │
│                      ▼                                             │
│         ┌────────────────────────────────────────┐                │
│         │   FastAPI Backend (REST + WebSocket)   │                │
│         │   Port: 8000                           │                │
│         ├────────────────────────────────────────┤                │
│         │  • /api/v1/cases                       │                │
│         │  • /api/v1/scans                       │                │
│         │  • /api/v1/investigations              │                │
│         │  • /api/v1/modules                     │                │
│         │  • /api/v1/graph                       │                │
│         │  • /ws/scan/{scan_id}                  │                │
│         └────────────┬───────────────────────────┘                │
│                      │                                             │
│                      ▼                                             │
│         ┌────────────────────────────────────────┐                │
│         │   arq Task Queue (Redis-backed)        │                │
│         ├────────────────────────────────────────┤                │
│         │  • Async module execution              │                │
│         │  • Concurrent API calls                │                │
│         │  • Progress tracking                   │                │
│         │  • Error isolation                     │                │
│         └────────────┬───────────────────────────┘                │
│                      │                                             │
│                      ▼                                             │
│         ┌────────────────────────────────────────┐                │
│         │   OSINT Module System                  │                │
│         ├────────────────────────────────────────┤                │
│         │  • Domain Intelligence                 │                │
│         │  • IP Investigation                    │                │
│         │  • Email OSINT                         │                │
│         │  • Blockchain Analysis                 │                │
│         │  • Geolocation                         │                │
│         │  • IoC Analysis                        │                │
│         └────────────┬───────────────────────────┘                │
│                      │                                             │
│                      ▼                                             │
│         ┌────────────────────────────────────────┐                │
│         │   Data Layer                           │                │
│         ├────────────────────────────────────────┤                │
│         │  PostgreSQL 16  │  Redis 7             │                │
│         │  • Cases        │  • Task queue        │                │
│         │  • Scans        │  • WebSocket events  │                │
│         │  • Indicators   │  • API cache         │                │
│         │  • Edges        │  • Rate limiting     │                │
│         │  • Evidence     │                      │                │
│         └────────────────────────────────────────┘                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Specifications

### 1. Frontend (Vue 3 + TypeScript)

**Technology Stack:**
- Vue 3.4+ (Composition API)
- TypeScript 5.4+
- Vite 5.3+ (build tool)
- Pinia 2.2+ (state management)
- Vue Router 4.3+
- Tailwind CSS 3.4+ (styling)
- Cytoscape.js 3.30+ (graph visualization)

**Project Structure:**
```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts              # Axios/fetch wrapper
│   │   ├── cases.ts               # Case API calls
│   │   ├── scans.ts               # Scan API calls
│   │   ├── investigations.ts      # Investigation API
│   │   └── websocket.ts           # WebSocket client
│   ├── components/
│   │   ├── AppSidebar.vue         # Main navigation
│   │   ├── GraphCanvas.vue        # Cytoscape graph (from IdentiAi)
│   │   ├── LiveFeed.vue           # WebSocket event stream
│   │   ├── CaseCard.vue           # Case list item
│   │   ├── ScanLauncher.vue       # Module selector + launch
│   │   ├── NodeDetailPanel.vue    # Selected node info
│   │   └── InvestigationTools.vue # Manual graph editing
│   ├── views/
│   │   ├── DashboardView.vue      # Overview + stats
│   │   ├── CasesView.vue          # Case management (from IdentiAi)
│   │   ├── ScansView.vue          # Scan history
│   │   ├── InvestigationView.vue  # Graph + live feed
│   │   ├── ModulesView.vue        # Available OSINT modules
│   │   ├── EvidenceView.vue       # Evidence tracking (from IdentiAi)
│   │   ├── SourcesView.vue        # API connector config (from IdentiAi)
│   │   ├── AIAnalystView.vue      # LLM integration (from IdentiAi)
│   │   └── ReportsView.vue        # Export + reporting
│   ├── stores/
│   │   ├── caseStore.ts           # Case state
│   │   ├── scanStore.ts           # Scan state
│   │   ├── graphStore.ts          # Graph data
│   │   └── authStore.ts           # Authentication (future)
│   ├── types/
│   │   ├── case.ts                # Case interfaces
│   │   ├── scan.ts                # Scan interfaces
│   │   ├── indicator.ts           # Node/edge types
│   │   └── module.ts              # Module metadata
│   ├── router/
│   │   └── index.ts               # Route definitions
│   ├── App.vue
│   └── main.ts
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

**Key Features (Inherited from IdentiAi):**
- Dark tactical UI theme
- Cytoscape.js graph with SVG icon nodes
- Case management with intake forms
- Evidence tracking with chain of custody
- API source configuration panel
- AI analyst integration (LLM config)
- Export engine (JSON/Markdown)
- WebSocket live feed sidebar

**New Features (OSIF-specific):**
- Domain/IP/Email investigation launchers
- Module marketplace/selector
- Attack surface visualization
- Blockchain transaction graphs
- Geolocation mapping integration

---

### 2. Backend API (FastAPI)

**Technology Stack:**
- FastAPI 0.111+
- Python 3.12+
- SQLAlchemy 2.0+ (async ORM)
- Alembic (migrations)
- Pydantic v2 (validation)
- arq (task queue)
- Redis 7+
- PostgreSQL 16+
- httpx (async HTTP client)
- python-dotenv

**Project Structure:**
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── cases.py           # Case CRUD endpoints
│   │   │   ├── scans.py           # Scan management
│   │   │   ├── investigations.py  # Investigation endpoints
│   │   │   ├── modules.py         # Module registry
│   │   │   ├── graph.py           # Graph data endpoints
│   │   │   ├── evidence.py        # Evidence tracking
│   │   │   └── websocket.py       # WebSocket endpoints
│   │   └── deps.py                # Dependency injection
│   ├── core/
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── security.py            # Auth (future)
│   │   └── database.py            # DB session management
│   ├── models/
│   │   ├── case.py                # Case ORM model
│   │   ├── scan.py                # Scan ORM model
│   │   ├── indicator.py           # Indicator (node) model
│   │   ├── edge.py                # Edge (relationship) model
│   │   └── evidence.py            # Evidence model
│   ├── schemas/
│   │   ├── case.py                # Case Pydantic schemas
│   │   ├── scan.py                # Scan schemas
│   │   ├── indicator.py           # Indicator schemas
│   │   ├── edge.py                # Edge schemas
│   │   └── module.py              # Module metadata schemas
│   ├── modules/
│   │   ├── base.py                # BaseOSINTModule abstract class
│   │   ├── registry.py            # Module auto-discovery
│   │   ├── domain/
│   │   │   ├── dns_records.py
│   │   │   ├── subdomain_enum.py
│   │   │   ├── email_hunter.py
│   │   │   └── tech_stack.py
│   │   ├── ip/
│   │   │   ├── geolocation.py
│   │   │   ├── shodan_lookup.py
│   │   │   └── abuseipdb.py
│   │   ├── email/
│   │   │   ├── breach_check.py
│   │   │   ├── email_intel.py
│   │   │   └── gravatar.py
│   │   ├── blockchain/
│   │   │   ├── bitcoin.py
│   │   │   └── ethereum.py
│   │   └── geolocation/
│   │       └── wifi_lookup.py
│   ├── services/
│   │   ├── scan_service.py        # Scan orchestration
│   │   ├── graph_service.py       # Graph operations
│   │   ├── auto_linker.py         # Cross-correlation
│   │   └── export_service.py      # Report generation
│   ├── tasks/
│   │   ├── worker.py              # arq worker config
│   │   └── scan_tasks.py          # Async scan execution
│   ├── main.py                    # FastAPI app factory
│   └── __init__.py
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── .env.example
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

**API Endpoints:**

```
# Cases
POST   /api/v1/cases                    # Create case
GET    /api/v1/cases                    # List cases
GET    /api/v1/cases/{case_id}          # Get case details
PUT    /api/v1/cases/{case_id}          # Update case
DELETE /api/v1/cases/{case_id}          # Delete case

# Scans
POST   /api/v1/scans                    # Launch scan
GET    /api/v1/scans                    # List scans
GET    /api/v1/scans/{scan_id}          # Get scan details
DELETE /api/v1/scans/{scan_id}          # Cancel/delete scan
GET    /api/v1/scans/{scan_id}/export   # Export scan results

# Investigations (Graph)
GET    /api/v1/investigations/{inv_id}/graph      # Get graph data
POST   /api/v1/investigations/{inv_id}/nodes      # Add manual node
POST   /api/v1/investigations/{inv_id}/edges      # Add manual edge
DELETE /api/v1/investigations/{inv_id}/nodes/{id} # Delete node
PUT    /api/v1/investigations/{inv_id}/clear      # Clear graph

# Modules
GET    /api/v1/modules                  # List available modules
GET    /api/v1/modules/{module_id}      # Get module details

# Evidence
POST   /api/v1/evidence                 # Add evidence
GET    /api/v1/evidence                 # List evidence
GET    /api/v1/evidence/{evidence_id}   # Get evidence details
PUT    /api/v1/evidence/{evidence_id}   # Update evidence
DELETE /api/v1/evidence/{evidence_id}   # Delete evidence

# WebSocket
WS     /ws/scan/{scan_id}               # Live scan updates

# Health
GET    /health                          # Liveness probe
GET    /ready                           # Readiness probe (DB + Redis)
```

---

### 3. Database Schema (PostgreSQL 16)

```sql
-- Cases (Investigation containers)
CREATE TABLE cases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number     VARCHAR(50) UNIQUE NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'open',
    priority        VARCHAR(20) NOT NULL DEFAULT 'medium',
    case_type       VARCHAR(50),
    assigned_to     VARCHAR(100),
    client          VARCHAR(100),
    jurisdiction    VARCHAR(100),
    target_name     VARCHAR(255),
    target_aliases  TEXT[],
    target_location VARCHAR(255),
    target_dob      DATE,
    tags            TEXT[],
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at       TIMESTAMPTZ
);

-- Scans (OSINT module execution jobs)
CREATE TABLE scans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id         UUID REFERENCES cases(id) ON DELETE CASCADE,
    seed_value      TEXT NOT NULL,
    seed_kind       VARCHAR(50) NOT NULL,
    modules         TEXT[] NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'queued',
    progress        INTEGER DEFAULT 0,
    total_modules   INTEGER DEFAULT 0,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ
);

-- Indicators (Graph nodes)
CREATE TABLE indicators (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind            VARCHAR(50) NOT NULL,
    value           TEXT NOT NULL,
    label           VARCHAR(255),
    metadata        JSONB DEFAULT '{}',
    confidence      NUMERIC(4,3) CHECK (confidence BETWEEN 0 AND 1),
    first_seen      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_verified   TIMESTAMPTZ,
    UNIQUE (kind, value)
);

CREATE INDEX idx_indicators_kind ON indicators(kind);
CREATE INDEX idx_indicators_value ON indicators(value);
CREATE INDEX idx_indicators_metadata ON indicators USING GIN(metadata);

-- Edges (Graph relationships)
CREATE TABLE edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    src_id          UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    dst_id          UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    relationship    VARCHAR(50) NOT NULL,
    confidence      NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source_module   VARCHAR(100) NOT NULL,
    evidence        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (src_id, dst_id, relationship, source_module)
);

CREATE INDEX idx_edges_src ON edges(src_id);
CREATE INDEX idx_edges_dst ON edges(dst_id);
CREATE INDEX idx_edges_relationship ON edges(relationship);

-- Scan findings (links scans to discovered edges)
CREATE TABLE scan_findings (
    scan_id         UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    edge_id         UUID NOT NULL REFERENCES edges(id) ON DELETE CASCADE,
    discovered_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (scan_id, edge_id)
);

-- Evidence (chain of custody tracking)
CREATE TABLE evidence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id         UUID REFERENCES cases(id) ON DELETE CASCADE,
    scan_id         UUID REFERENCES scans(id) ON DELETE SET NULL,
    title           VARCHAR(255) NOT NULL,
    evidence_type   VARCHAR(50) NOT NULL,
    source_url      TEXT,
    description     TEXT,
    file_path       TEXT,
    file_hash       VARCHAR(64),
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    collected_by    VARCHAR(100),
    chain_of_custody JSONB DEFAULT '[]',
    confidence      VARCHAR(20),
    tags            TEXT[],
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_evidence_case ON evidence(case_id);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);
```

---

### 4. Module System Architecture

**Base Module Pattern:**

```python
from abc import ABC, abstractmethod
from typing import ClassVar, List
from pydantic import BaseModel

class DiscoveryResult(BaseModel):
    src_value: str
    src_kind: str
    dst_value: str
    dst_kind: str
    relationship: str
    confidence: float
    evidence: dict
    source_module: str

class BaseOSINTModule(ABC):
    """Abstract base class for all OSINT modules"""
    
    MODULE_ID: ClassVar[str]
    DISPLAY_NAME: ClassVar[str]
    DESCRIPTION: ClassVar[str]
    CATEGORY: ClassVar[str]  # domain, ip, email, blockchain, etc.
    ACCEPTS: ClassVar[List[str]]  # Indicator kinds this module accepts
    REQUIRES_API_KEY: ClassVar[bool] = False
    API_KEY_ENV_VAR: ClassVar[str] = ""
    
    @abstractmethod
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute OSINT collection and return discoveries"""
        pass
    
    def validate_config(self, config: dict) -> bool:
        """Validate module configuration"""
        if self.REQUIRES_API_KEY:
            return bool(os.getenv(self.API_KEY_ENV_VAR))
        return True
```

**Module Registry (Auto-discovery):**

```python
# backend/app/modules/registry.py
import importlib
import pkgutil
from typing import Dict, Type
from .base import BaseOSINTModule

PLUGIN_REGISTRY: Dict[str, Type[BaseOSINTModule]] = {}

def register_module(cls: Type[BaseOSINTModule]):
    """Decorator to auto-register modules"""
    PLUGIN_REGISTRY[cls.MODULE_ID] = cls
    return cls

def discover_modules():
    """Auto-discover all modules in modules/ directory"""
    import app.modules as modules_package
    
    for importer, modname, ispkg in pkgutil.walk_packages(
        modules_package.__path__,
        prefix=f"{modules_package.__name__}."
    ):
        if not modname.endswith('.base') and not modname.endswith('.registry'):
            importlib.import_module(modname)
    
    return PLUGIN_REGISTRY
```

**Example Module Implementation:**

```python
# backend/app/modules/domain/dns_records.py
from ..base import BaseOSINTModule, DiscoveryResult, register_module
import dns.resolver

@register_module
class DNSRecordsModule(BaseOSINTModule):
    MODULE_ID = "dns_records"
    DISPLAY_NAME = "DNS Records Lookup"
    DESCRIPTION = "Resolve A, AAAA, MX, TXT records for a domain"
    CATEGORY = "domain"
    ACCEPTS = ["domain"]
    REQUIRES_API_KEY = False
    
    async def execute(self, target: str, kind: str, **kwargs) -> List[DiscoveryResult]:
        results = []
        
        # A records
        try:
            answers = dns.resolver.resolve(target, 'A', lifetime=5)
            for rdata in answers:
                results.append(DiscoveryResult(
                    src_value=target,
                    src_kind="domain",
                    dst_value=str(rdata),
                    dst_kind="ip",
                    relationship="resolves_to",
                    confidence=1.0,
                    evidence={"record_type": "A"},
                    source_module=self.MODULE_ID
                ))
        except Exception as e:
            pass  # Log but don't fail
        
        # MX records
        try:
            mx_answers = dns.resolver.resolve(target, 'MX', lifetime=5)
            for rdata in mx_answers:
                results.append(DiscoveryResult(
                    src_value=target,
                    src_kind="domain",
                    dst_value=str(rdata.exchange).rstrip('.'),
                    dst_kind="host",
                    relationship="mail_server",
                    confidence=1.0,
                    evidence={"record_type": "MX", "priority": rdata.preference},
                    source_module=self.MODULE_ID
                ))
        except Exception as e:
            pass
        
        return results
```

---

### 5. Task Queue (arq + Redis)

**Worker Configuration:**

```python
# backend/app/tasks/worker.py
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings

async def startup(ctx):
    """Worker startup - initialize shared resources"""
    ctx['http_client'] = httpx.AsyncClient(timeout=30.0)
    ctx['db'] = await get_async_session()

async def shutdown(ctx):
    """Worker shutdown - cleanup"""
    await ctx['http_client'].aclose()
    await ctx['db'].close()

class WorkerSettings:
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    functions = [run_scan_task]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = settings.WORKER_CONCURRENCY
    job_timeout = 300  # 5 minutes per module
```

**Scan Task:**

```python
# backend/app/tasks/scan_tasks.py
async def run_scan_task(ctx, scan_id: str, module_id: str, target: str, kind: str):
    """Execute a single OSINT module"""
    from app.modules.registry import PLUGIN_REGISTRY
    from app.services.graph_service import GraphService
    
    # Publish start event
    await publish_event(scan_id, {
        "type": "module_start",
        "module_id": module_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        # Load module
        module_class = PLUGIN_REGISTRY[module_id]
        module = module_class()
        
        # Execute
        results = await module.execute(
            target=target,
            kind=kind,
            http_client=ctx['http_client'],
            config={}
        )
        
        # Persist results
        graph_service = GraphService(ctx['db'])
        for result in results:
            edge = await graph_service.add_discovery(scan_id, result)
            
            # Publish discovery event
            await publish_event(scan_id, {
                "type": "discovery",
                "module_id": module_id,
                "payload": result.dict(),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Publish completion
        await publish_event(scan_id, {
            "type": "module_done",
            "module_id": module_id,
            "discoveries": len(results),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        # Publish error
        await publish_event(scan_id, {
            "type": "module_error",
            "module_id": module_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise

async def publish_event(scan_id: str, event: dict):
    """Publish event to Redis Stream for WebSocket broadcast"""
    redis = await get_redis()
    await redis.xadd(
        f"scan:{scan_id}:events",
        {"data": json.dumps(event)},
        maxlen=1000
    )
```

---

### 6. CLI Integration

**Enhanced CLI with API Client:**

```python
# osif (enhanced)
class OsifConsole(FrameworkConsole):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = OSIFAPIClient(base_url="http://localhost:8000")
    
    def do_scan(self, args):
        """Launch scan via API: scan <target> <module1,module2,...>"""
        parts = args.split()
        if len(parts) < 2:
            print("Usage: scan <target> <module1,module2,...>")
            return
        
        target = parts[0]
        modules = parts[1].split(',')
        
        # Create scan via API
        response = self.api_client.create_scan(
            seed_value=target,
            seed_kind="domain",  # Auto-detect or prompt
            modules=modules
        )
        
        scan_id = response['id']
        print(f"Scan created: {scan_id}")
        print(f"View at: http://localhost:5173/scans/{scan_id}")
        
        # Optional: Stream results to CLI
        if input("Stream results? [y/N]: ").lower() == 'y':
            self.stream_scan_results(scan_id)
```

---

## 🔄 Data Flow Diagrams

### Scan Execution Flow

```
User (Frontend/CLI)
    ↓
POST /api/v1/scans
    ↓
FastAPI creates Scan record (status=queued)
    ↓
Enqueue tasks to arq (one per module)
    ↓
Return scan_id to client
    ↓
Client opens WebSocket /ws/scan/{scan_id}
    ↓
arq workers execute modules concurrently
    ↓
Each discovery → GraphService.add_discovery()
    ↓
Persist Indicator + Edge to PostgreSQL
    ↓
Publish event to Redis Stream
    ↓
WebSocket handler reads stream → broadcasts to client
    ↓
Frontend updates graph in real-time
```

### Case Management Flow

```
User creates case
    ↓
POST /api/v1/cases
    ↓
Case record created in PostgreSQL
    ↓
User launches scan within case context
    ↓
POST /api/v1/scans (with case_id)
    ↓
Scan linked to case via case_id FK
    ↓
Discoveries auto-linked to case
    ↓
User adds manual evidence
    ↓
POST /api/v1/evidence (with case_id)
    ↓
Evidence record with chain of custody
    ↓
Export case report
    ↓
GET /api/v1/cases/{case_id}/export
    ↓
Generate PDF/Markdown with all scans + evidence
```

---

## 🔐 Security Architecture

### Authentication & Authorization (Phase 2)

```
┌─────────────────────────────────────┐
│   JWT-based Authentication          │
├─────────────────────────────────────┤
│  • POST /api/v1/auth/login          │
│  • POST /api/v1/auth/refresh        │
│  • Access token (15 min)            │
│  • Refresh token (7 days)           │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│   Role-Based Access Control         │
├─────────────────────────────────────┤
│  • admin: full access               │
│  • analyst: read + create scans     │
│  • viewer: read-only                │
└─────────────────────────────────────┘
```

### API Key Management

- All external API keys in `.env` (never committed)
- Encrypted at rest in database (future)
- Per-user API key quotas (future)
- Rate limiting per API key

### Data Protection

- PostgreSQL row-level security (RLS) for multi-tenancy
- Evidence files stored with SHA-256 hashes
- Chain of custody audit trail
- PII redaction in logs

---

## 📊 Performance & Scalability

### Current Bottlenecks (v1)

1. ❌ In-memory storage (no persistence)
2. ❌ Synchronous API calls (blocking)
3. ❌ Single-threaded Flask dev server
4. ❌ No caching layer

### v2 Improvements

1. ✅ PostgreSQL persistence with indexes
2. ✅ Async/await with httpx
3. ✅ arq worker pool (configurable concurrency)
4. ✅ Redis caching for API responses
5. ✅ Connection pooling (SQLAlchemy + Redis)

### Scalability Targets

| Metric | Target |
|--------|--------|
| Concurrent scans | 50+ |
| Graph nodes | 10,000+ per investigation |
| API response time | <200ms (p95) |
| WebSocket latency | <50ms |
| Module execution | 4-8 concurrent per worker |
| Database connections | 20 pool size |

### Horizontal Scaling Path

```
Phase 1: Single server (MVP)
    ↓
Phase 2: Multiple workers + Redis Sentinel
    ↓
Phase 3: Load balancer + multiple API instances
    ↓
Phase 4: PostgreSQL read replicas
    ↓
Phase 5: Kubernetes deployment
```

---

## 🧪 Testing Strategy

### Test Pyramid

```
         ┌─────────────┐
         │  E2E Tests  │  ← Playwright (frontend + API)
         └─────────────┘
       ┌─────────────────┐
       │ Integration Tests│  ← API endpoints + DB
       └─────────────────┘
    ┌──────────────────────┐
    │    Unit Tests        │  ← Modules, services, utils
    └──────────────────────┘
```

### Coverage Targets

- **Unit tests**: 80%+ coverage
- **Integration tests**: All API endpoints
- **E2E tests**: Critical user flows

### Test Files

```
backend/tests/
├── unit/
│   ├── test_modules.py           # Module execution
│   ├── test_graph_service.py     # Graph operations
│   └── test_auto_linker.py       # Correlation logic
├── integration/
│   ├── test_scan_api.py          # Scan endpoints
│   ├── test_case_api.py          # Case endpoints
│   └── test_websocket.py         # WebSocket events
└── e2e/
    └── test_scan_flow.py         # Full scan lifecycle

frontend/tests/
├── unit/
│   ├── GraphCanvas.spec.ts
│   └── stores/scanStore.spec.ts
└── e2e/
    ├── case-management.spec.ts
    └── scan-execution.spec.ts
```

---

## 🚀 Deployment Architecture

### Development Environment

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: osif_dev
      POSTGRES_USER: osif
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://osif:dev_password@postgres:5432/osif_dev
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

  worker:
    build: ./backend
    command: arq app.tasks.worker.WorkerSettings
    environment:
      DATABASE_URL: postgresql+asyncpg://osif:dev_password@postgres:5432/osif_dev
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    command: npm run dev -- --host 0.0.0.0
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
  redis_data:
```

### Production Environment

```
┌─────────────────────────────────────┐
│         Nginx (Reverse Proxy)       │
│         SSL Termination             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    Frontend (Static Files)          │
│    Served by Nginx                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    Gunicorn + Uvicorn Workers       │
│    (4-8 workers)                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    PostgreSQL 16 (Primary)          │
│    + Read Replicas (optional)       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    Redis Sentinel (HA)              │
│    + Redis Cluster (optional)       │
└─────────────────────────────────────┘
```

---

## 📅 Migration Plan

### Phase 1: Foundation (Weeks 1-2)

- [ ] Initialize FastAPI project structure
- [ ] Set up PostgreSQL schema + Alembic
- [ ] Implement base module system
- [ ] Create module registry with auto-discovery
- [ ] Port 3-5 core modules (DNS, IP lookup, email)

### Phase 2: API Layer (Weeks 3-4)

- [ ] Implement all REST endpoints
- [ ] Add WebSocket support
- [ ] Integrate arq task queue
- [ ] Add health/readiness endpoints
- [ ] Write API integration tests

### Phase 3: Frontend (Weeks 5-6)

- [ ] Fork IdentiAi frontend
- [ ] Adapt components for OSIF use cases
- [ ] Implement API client layer
- [ ] Add OSIF-specific views (modules, sources)
- [ ] WebSocket integration for live feed

### Phase 4: CLI Integration (Week 7)

- [ ] Add API client to CLI
- [ ] Implement `scan` command
- [ ] Add `case` management commands
- [ ] Backward compatibility layer

### Phase 5: Testing & Documentation (Week 8)

- [ ] Write comprehensive tests
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide
- [ ] Deployment guide

### Phase 6: Migration & Deprecation (Week 9-10)

- [ ] Data migration scripts (if needed)
- [ ] Parallel deployment (v1 + v2)
- [ ] User acceptance testing
- [ ] Deprecate old Flask app
- [ ] Remove `templates/` and `static/` directories

---

## 🔧 Configuration Management

### Environment Variables

```bash
# ── Database ──────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/osif
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ── Redis ─────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# ── API Server ────────────────────────────────────────────────────────
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ── Worker ────────────────────────────────────────────────────────────
WORKER_CONCURRENCY=4
REQUEST_DELAY_MS=500

# ── External APIs (from current OSIF) ─────────────────────────────────
VT_API=
SHODAN_API_KEY=
ABUSEIPDB_API_KEY=
HUNTER_API_KEY=
TOMBA_API_KEY=
TOMBA_SECRET_KEY=
CENSYS_APPID=
CENSYS_SECRET=
ABUSECH_API_KEY=
BITCOINABUSE_API_KEY=
WIGLE_API_NAME=
WIGLE_API_TOKEN=
SECURITY_TRAIL_API=

# ── Frontend ──────────────────────────────────────────────────────────
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# ── Security (Phase 2) ────────────────────────────────────────────────
SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 📚 Technology Decisions

### Why FastAPI over Flask?

| Aspect | Flask (v1) | FastAPI (v2) |
|--------|-----------|--------------|
| Performance | Synchronous | Async/await native |
| Type safety | None | Pydantic validation |
| API docs | Manual | Auto-generated (OpenAPI) |
| WebSocket | Flask-SocketIO | Native support |
| Modern Python | 3.7+ | 3.12+ with type hints |

### Why PostgreSQL over MongoDB?

- Relational graph queries (recursive CTEs)
- ACID compliance for case management
- Better tooling (pgAdmin, DBeaver)
- Strong typing with SQLAlchemy

### Why arq over Celery?

- Pure async (no threading)
- Simpler configuration
- Better Redis integration
- Smaller footprint

### Why Vue 3 over React?

- Already proven in IdentiAi
- Composition API similar to React hooks
- Better TypeScript support than Vue 2
- Smaller bundle size

---

## 🎯 Success Metrics

### Technical Metrics

- [ ] API response time p95 < 200ms
- [ ] WebSocket message latency < 50ms
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities
- [ ] Database query time p95 < 100ms

### User Experience Metrics

- [ ] Scan launch to first result < 3s
- [ ] Graph rendering for 1000 nodes < 500ms
- [ ] Case creation < 2s
- [ ] Export generation < 5s

### Operational Metrics

- [ ] Uptime > 99.5%
- [ ] Worker error rate < 1%
- [ ] Database connection pool utilization < 80%
- [ ] Redis memory usage < 2GB

---

## 🚧 Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Module migration complexity** | High | Port modules incrementally, test each |
| **Data migration from v1** | Medium | v1 has no persistence, fresh start OK |
| **Learning curve (FastAPI)** | Medium | Excellent docs, similar to Flask |
| **WebSocket scaling** | High | Use Redis pub/sub for multi-instance |
| **Graph performance** | High | PostgreSQL indexes + pagination |
| **API key management** | Medium | Vault integration (Phase 2) |

---

## 📖 References

### Architecture Inspiration

- **IdentiAi**: Case management, graph UI, dark theme
- **OSIF v1**: Module system, CLI interface, OSINT sources
- **Maltego**: Graph-based investigation paradigm
- **Metasploit**: CLI command structure

### Technology Documentation

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [arq](https://arq-docs.helpmanual.io/)
- [Vue 3](https://vuejs.org/)
- [Cytoscape.js](https://js.cytoscape.org/)
- [PostgreSQL 16](https://www.postgresql.org/docs/16/)

---

## ✅ Approval & Sign-off

**Prepared by:** Chief Architect (AI Agent)  
**Date:** 2026-06-30  
**Status:** ✅ Ready for Implementation

**Next Steps:**
1. Review and approve this specification
2. Set up development environment
3. Begin Phase 1 implementation
4. Weekly progress reviews

---

**END OF SPECIFICATION**
