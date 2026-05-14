# OSIF Architecture Documentation

**Project:** OSIF (Open Source Intelligence Framework)  
**Version:** 2.0 (Web Interface)  
**Last Updated:** 2026-05-13

---

## 🏗️ **System Architecture Overview**

OSIF is a dual-interface OSINT platform combining a traditional CLI (Metasploit-style) with a modern web-based graph visualization interface.

```
┌─────────────────────────────────────────────────────────────┐
│                         OSIF Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │   CLI Interface  │         │   Web Interface         │  │
│  │   (osif script)  │◄───────►│   (web_server.py)       │  │
│  │                  │         │                         │  │
│  │  • Metasploit-   │         │  • Flask REST API       │  │
│  │    style console │         │  • Graph visualization  │  │
│  │  • Module system │         │  • Real-time updates    │  │
│  │  • Background    │         │  • Export capabilities  │  │
│  │    web server    │         │                         │  │
│  └──────────────────┘         └─────────────────────────┘  │
│           │                              │                  │
│           └──────────┬───────────────────┘                  │
│                      ▼                                      │
│         ┌────────────────────────┐                         │
│         │   Module System        │                         │
│         ├────────────────────────┤                         │
│         │ • attack-surface/      │                         │
│         │ • blockchain/          │                         │
│         │ • email/               │                         │
│         │ • geolocation/         │                         │
│         │ • host_enum/           │                         │
│         │ • ioc/                 │                         │
│         │ • mobile/              │                         │
│         │ • source-code/         │                         │
│         │ • web_enum/            │                         │
│         └────────────────────────┘                         │
│                      │                                      │
│                      ▼                                      │
│         ┌────────────────────────┐                         │
│         │   External APIs        │                         │
│         ├────────────────────────┤                         │
│         │ • VirusTotal           │                         │
│         │ • Shodan               │                         │
│         │ • AbuseIPDB            │                         │
│         │ • Hunter.io / Tomba    │                         │
│         │ • Censys               │                         │
│         │ • WiGLE                │                         │
│         │ • SecurityTrails       │                         │
│         │ • Abuse.ch             │                         │
│         │ • Bitcoin APIs         │                         │
│         └────────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 **Component Breakdown**

### **1. CLI Interface (`osif`)**

**Technology:** Python 3, sploitkit framework, tinyscript

**Responsibilities:**
- Command-line interface for OSINT operations
- Module discovery and loading
- Background web server management
- Port conflict detection and auto-increment
- User interaction and command processing

**Key Features:**
- Metasploit-style command structure
- Tab completion
- Module options configuration
- Background subprocess management
- Graceful shutdown handling

**File:** `/osif`

---

### **2. Web Interface (`web_server.py`)**

**Technology:** Flask, Python 3, vis.js (frontend)

**Responsibilities:**
- RESTful API for OSINT operations
- Graph data management (nodes & edges)
- Real-time investigation orchestration
- Data export functionality
- Browser-based visualization

**Architecture Pattern:** MVC-like
- **Routes** → API endpoints
- **Logic** → Investigation functions
- **Data** → In-memory graph storage

**API Endpoints:**
```
GET  /                          → Main interface
GET  /api/graph                 → Get graph data
POST /api/graph/clear           → Clear graph
POST /api/investigate/domain    → Domain investigation
POST /api/investigate/ip        → IP investigation
POST /api/investigate/email     → Email investigation
POST /api/investigate/bitcoin   → Bitcoin investigation
GET  /api/node/<id>             → Node details
GET  /api/export/graph          → Export as JSON
```

**File:** `/web_server.py`

---

### **3. Module System**

**Technology:** Python 3, sploitkit Module class

**Structure:**
```
modules/
├── attack-surface/     # Network exposure analysis
├── blockchain/         # Cryptocurrency investigations
├── email/              # Email OSINT
├── geolocation/        # Location tracking
├── host_enum/          # Host enumeration
├── ioc/                # Indicators of Compromise
│   ├── abusech.py      # Malware hash lookup
│   ├── abuseipdb.py    # IP reputation
│   └── virustotal.py   # Multi-engine scanning
├── mobile/             # Mobile device OSINT
├── source-code/        # Code repository analysis
└── web_enum/           # Web application enumeration
```

**Module Pattern:**
```python
class ModuleName(Module):
    """Module description"""
    
    config = Config({
        Option('PARAM', 'Description', required): type(default)
    })
    
    def run(self):
        # Investigation logic
        pass
```

---

### **4. Frontend (Web UI)**

**Technology:** HTML5, CSS3, JavaScript, vis.js

**Files:**
- `templates/index.html` - Main interface
- `static/css/style.css` - Styling
- `static/js/graph.js` - Graph visualization
- `static/js/app.js` - Application logic

**Features:**
- Interactive graph with zoom/pan
- Node filtering and search
- Real-time updates
- Click for details, double-click to investigate
- Export to JSON

---

## 🔄 **Data Flow**

### **Domain Investigation Flow**

```
User Input (domain)
    ↓
Web API: POST /api/investigate/domain
    ↓
Create domain node
    ↓
┌─────────────────────────────────────┐
│ Parallel API Calls:                 │
│ 1. Tomba (emails)                   │
│ 2. DNS resolver (A, MX records)     │
│ 3. crt.sh (subdomains via CT logs)  │
└─────────────────────────────────────┘
    ↓
Create child nodes (emails, IPs, hosts)
    ↓
Create edges (relationships)
    ↓
Return graph update to frontend
    ↓
vis.js renders new nodes/edges
```

### **IP Investigation Flow**

```
User Input (IP address)
    ↓
Web API: POST /api/investigate/ip
    ↓
Create IP node
    ↓
┌─────────────────────────────────────┐
│ Sequential API Calls:               │
│ 1. ip-api.com (geolocation, ISP)    │
│ 2. AbuseIPDB (reputation)           │
│ 3. Shodan (ports, hostnames)        │
└─────────────────────────────────────┘
    ↓
Create child nodes (location, ISP, threat)
    ↓
Update IP node with reputation data
    ↓
Return graph update
    ↓
Render with threat indicators
```

---

## 🗄️ **Data Storage**

### **Current: In-Memory**

```python
graph_data = {
    "nodes": [
        {
            "id": "domain_example.com",
            "label": "example.com",
            "type": "domain",
            "data": {...},
            "timestamp": "2026-05-13T22:00:00"
        }
    ],
    "edges": [
        {
            "from": "domain_example.com",
            "to": "email_user@example.com",
            "relationship": "has_email",
            "data": {...},
            "timestamp": "2026-05-13T22:00:00"
        }
    ]
}
```

**Limitations:**
- Data lost on server restart
- No persistence across sessions
- Single-user only
- No search/query capabilities

**Future: Database (Recommended)**
- PostgreSQL for relational data
- Redis for caching API responses
- Full-text search
- Multi-user support
- Investigation history

---

## 🔌 **External Integrations**

### **API Services**

| Service | Purpose | Rate Limits | Cost |
|---------|---------|-------------|------|
| **VirusTotal** | File/URL/IP/domain scanning | 4 req/min (free) | Free tier available |
| **Shodan** | Internet-wide port scanning | 1 req/sec | $59/month |
| **AbuseIPDB** | IP reputation | 1000 req/day (free) | Free tier available |
| **Hunter.io** | Email discovery | 25 req/month (free) | Freemium |
| **Tomba** | Email finder | 50 req/month (free) | Freemium |
| **Censys** | Internet scanning | 250 req/month (free) | Freemium |
| **WiGLE** | WiFi geolocation | Unlimited (free) | Free |
| **SecurityTrails** | DNS/WHOIS history | 50 req/month (free) | Freemium |
| **Abuse.ch** | Malware intelligence | Unlimited (free) | Free |

### **Free/Public APIs**

- **ip-api.com** - IP geolocation (45 req/min)
- **crt.sh** - Certificate Transparency (unlimited)
- **dns.resolver** - DNS queries (local)
- **blockchain.info** - Bitcoin data (unlimited)

---

## 🔐 **Security Considerations**

### **API Key Management**
- Stored in `.env` file (gitignored)
- Loaded via `python-dotenv`
- Never exposed in client-side code
- Environment variable validation

### **Web Server**
- CORS enabled (development only)
- No authentication (currently)
- Debug mode (development only)
- Input validation needed

### **Future Security Enhancements**
- [ ] User authentication (JWT)
- [ ] API key encryption at rest
- [ ] Rate limiting per user
- [ ] Audit logging
- [ ] HTTPS enforcement
- [ ] CSRF protection
- [ ] Input sanitization

---

## 🚀 **Deployment Architecture**

### **Development**
```
Local Machine
├── Python virtual environment
├── Flask development server (port 5001+)
├── In-memory data storage
└── Direct API calls
```

### **Production (Recommended)**
```
┌─────────────────────────────────────┐
│         Load Balancer (Nginx)       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    WSGI Server (Gunicorn/uWSGI)     │
│    Multiple worker processes        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│         Flask Application           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  PostgreSQL + Redis                 │
│  (Data + Cache)                     │
└─────────────────────────────────────┘
```

---

## 📊 **Performance Characteristics**

### **Current Bottlenecks**
1. **Sequential API calls** - No async/await
2. **In-memory storage** - Limited scalability
3. **No caching** - Repeated API calls
4. **Single-threaded** - Flask development server

### **Optimization Opportunities**
1. Implement async/await for parallel API calls
2. Add Redis caching layer
3. Database persistence
4. Background job queue (Celery)
5. API response pagination

---

## 🧪 **Testing Strategy**

### **Current State**
- Manual testing only
- No automated tests

### **Recommended Test Coverage**
```
tests/
├── unit/
│   ├── test_modules.py          # Module functionality
│   ├── test_api_endpoints.py    # Web API
│   └── test_graph_operations.py # Graph management
├── integration/
│   ├── test_investigations.py   # End-to-end flows
│   └── test_api_integrations.py # External APIs
└── e2e/
    └── test_web_interface.py    # Browser automation
```

---

## 📈 **Scalability Considerations**

### **Current Limitations**
- Single server instance
- In-memory data (lost on restart)
- No horizontal scaling
- No load balancing

### **Scaling Path**
1. **Phase 1:** Database persistence
2. **Phase 2:** Redis caching
3. **Phase 3:** Async workers (Celery)
4. **Phase 4:** Horizontal scaling (multiple instances)
5. **Phase 5:** Microservices (if needed)

---

## 🔧 **Technology Stack Summary**

**Backend:**
- Python 3.12+
- Flask 2.3+
- sploitkit (CLI framework)
- tinyscript (CLI utilities)
- python-dotenv (config)
- requests (HTTP client)

**Frontend:**
- HTML5/CSS3/JavaScript
- vis.js (graph visualization)
- Vanilla JS (no framework)

**External:**
- Multiple OSINT APIs
- DNS resolution
- HTTP requests

**Infrastructure:**
- Virtual environment (venv)
- Git version control
- Environment-based configuration

---

## 📝 **Configuration Management**

### **Environment Variables (`.env`)**
```bash
# API Keys
VT_API=""
SHODAN_API_KEY=""
ABUSEIPDB_API_KEY=""
HUNTER_API_KEY=""
TOMBA_API_KEY=""
TOMBA_SECRET_KEY=""
CENSYS_APPID=""
CENSYS_SECRET=""
ABUSECH_API_KEY=""
BITCOINABUSE_API_KEY=""
WIGLE_API_NAME=""
WIGLE_API_TOKEN=""
SECURITY_TRAIL_API=""

# Web Server
SECRET_KEY=""
WEB_PORT=5000
FLASK_ENV="development"
```

### **Module Discovery**
- Automatic scanning of `modules/` directory
- sploitkit framework handles loading
- Module metadata from class definitions

---

## 🎯 **Design Principles**

1. **Modularity** - Pluggable module system
2. **Extensibility** - Easy to add new data sources
3. **Usability** - Both CLI and web interfaces
4. **Visualization** - Graph-based relationship mapping
5. **Open Source** - Community-driven development
6. **API-First** - RESTful design for integrations

---

## 🚧 **Known Technical Debt**

1. No database persistence
2. No authentication/authorization
3. No API rate limiting
4. No error recovery mechanisms
5. Limited input validation
6. No logging infrastructure
7. Synchronous API calls (blocking)
8. No test coverage
9. Hard-coded configuration values
10. No API documentation (Swagger/OpenAPI)

---

## 📚 **Further Reading**

- [sploitkit Documentation](https://github.com/dhondta/python-sploitkit)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [vis.js Network Documentation](https://visjs.github.io/vis-network/docs/network/)
- [OSINT Framework](https://osintframework.com/)
