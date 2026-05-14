# OSIF Web Interface - User Guide

## 🌐 Overview

The OSIF Web Interface provides a **Maltego-style graph visualization** for OSINT investigations. It allows you to:

- Visualize relationships between domains, IPs, emails, and other entities
- Interactively explore OSINT data through an intuitive graph interface
- Chain investigations by double-clicking nodes to expand them
- Export investigation graphs as JSON

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Make sure your `.env` file contains the necessary API keys:

```env
HUNTER_API_KEY="your_hunter_key"
SHODAN_API_KEY="your_shodan_key"
VT_API="your_virustotal_key"
TOMBA_API_KEY="your_tomba_key"
TOMBA_SECRET_KEY="your_tomba_secret"
```

### 3. Start the Web Server

```bash
python web_server.py
```

The server will automatically open your browser at `http://localhost:5000`

## 📊 Features

### Investigation Tools

#### 🌐 Domain Investigation
- **Input:** Domain name (e.g., `example.com`)
- **Discovers:**
  - Email addresses associated with the domain
  - DNS records and IP addresses
  - Subdomains
  - Technology stack (CMS, frameworks, libraries)

#### 🔌 IP Address Investigation
- **Input:** IP address (e.g., `8.8.8.8`)
- **Discovers:**
  - Geolocation information
  - ISP and organization
  - Open ports (requires Shodan API)
  - Hostnames
  - Associated services

#### 📧 Email Investigation
- **Input:** Email address (e.g., `user@example.com`)
- **Discovers:**
  - Associated domain
  - Domain relationships

#### ₿ Bitcoin Investigation
- **Input:** Bitcoin address
- **Discovers:**
  - Wallet balance
  - Total received/sent
  - Transaction count

### Graph Interaction

#### Single Click
- Click any node to view detailed information in the side panel
- See connections, relationships, and metadata

#### Double Click
- Double-click a node to expand and investigate it further
- Domain nodes → trigger domain investigation
- IP nodes → trigger IP investigation
- Email nodes → trigger email investigation

#### Navigation
- **Pan:** Click and drag the background
- **Zoom:** Use mouse wheel
- **Select Multiple:** Hold Ctrl/Cmd and click nodes

### Graph Controls

#### Clear Graph
Removes all nodes and edges from the current investigation

#### Export JSON
Downloads the current graph as a JSON file for:
- Backup
- Sharing with team members
- Import into other tools

#### Fit View
Automatically centers and scales the graph to fit the viewport

## 🎨 Node Types and Colors

| Node Type | Color | Icon | Description |
|-----------|-------|------|-------------|
| Domain | Blue | 🌐 | Domain names |
| Email | Red | ✉️ | Email addresses |
| IP | Green | 🔌 | IP addresses |
| Subdomain | Purple | 🌐 | Subdomains |
| Technology | Orange | ⚙️ | Web technologies |
| Location | Teal | 📍 | Geographic locations |
| ISP | Gray | 🏢 | Internet Service Providers |
| Port | Orange | 🔗 | Network ports |
| Bitcoin | Gold | ₿ | Bitcoin addresses |

## 🔄 Investigation Workflow

### Example: Domain Investigation

1. **Start with a Domain**
   ```
   Enter: target.com
   Click: Investigate
   ```

2. **Review Results**
   - Domain node appears in center
   - Connected emails, IPs, technologies appear around it

3. **Expand Investigation**
   - Double-click an IP node to investigate it
   - New nodes appear showing location, ISP, open ports

4. **Explore Email**
   - Click an email node to see details
   - Double-click to investigate the email

5. **Export Results**
   - Click "Export JSON" to save your investigation
   - Share with team or document findings

### Example: Multi-Level Investigation

```
Domain (example.com)
  ├─> Emails (john@example.com, admin@example.com)
  ├─> IPs (93.184.216.34)
  │     ├─> Location (Los Angeles, USA)
  │     ├─> ISP (EdgeCast Networks)
  │     └─> Ports (80, 443, 8080)
  ├─> Subdomains (api.example.com, mail.example.com)
  └─> Technologies (WordPress, MySQL, Cloudflare)
```

## 🔧 Advanced Features

### API Endpoints

The web server exposes REST APIs for programmatic access:

#### Get Graph Data
```bash
curl http://localhost:5000/api/graph
```

#### Investigate Domain
```bash
curl -X POST http://localhost:5000/api/investigate/domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

#### Clear Graph
```bash
curl -X POST http://localhost:5000/api/graph/clear
```

### Export Format

Exported JSON includes:
```json
{
  "graph": {
    "nodes": [
      {
        "id": "domain_example.com",
        "label": "example.com",
        "type": "domain",
        "data": {...},
        "timestamp": "2026-02-02T..."
      }
    ],
    "edges": [
      {
        "from": "domain_example.com",
        "to": "email_john@example.com",
        "relationship": "has_email",
        "timestamp": "2026-02-02T..."
      }
    ]
  },
  "exported_at": "2026-02-02T...",
  "node_count": 15,
  "edge_count": 18
}
```

## 🎯 Use Cases

### 1. Threat Intelligence
- Map out malicious infrastructure
- Identify related domains and IPs
- Track threat actor email addresses

### 2. Digital Footprint Analysis
- Discover organization's external attack surface
- Identify exposed services and technologies
- Map subdomain structure

### 3. Investigation Support
- Visual documentation of findings
- Easy sharing with team members
- Historical tracking of investigations

### 4. Reconnaissance
- Pre-engagement information gathering
- Technology stack identification
- Contact discovery

## 🔒 Security Notes

- The web server runs on `0.0.0.0:5000` by default (accessible from network)
- For production use, consider:
  - Adding authentication
  - Using HTTPS
  - Rate limiting API calls
  - Running behind a reverse proxy

## 🐛 Troubleshooting

### Web Server Won't Start
```bash
# Check if port 5000 is already in use
lsof -i :5000

# Use a different port
FLASK_RUN_PORT=8080 python web_server.py
```

### No Results for Investigations
- Verify API keys in `.env` file
- Check API rate limits
- Ensure internet connectivity

### Graph Not Loading
- Clear browser cache
- Check browser console for errors (F12)
- Verify Flask server is running

### Modules Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 📝 Tips & Best Practices

1. **Start Small:** Begin with one entity and expand gradually
2. **Use Double-Click:** Quickly expand investigations by double-clicking nodes
3. **Export Often:** Save your work regularly using Export JSON
4. **Clear When Needed:** Use Clear Graph to start fresh investigations
5. **Check Details:** Click nodes to see full metadata in the details panel
6. **API Keys:** More API keys = more comprehensive results

## 🔄 Integration with CLI

You can use both the web interface and CLI together:

1. Use web interface for **visual exploration**
2. Use CLI (`./osif`) for **detailed module execution**
3. Use API endpoints for **automation**

## 📚 Related Documentation

- [README.md](../README.md) - Main project documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute
- API Documentation: Check individual modules in `/modules`

## 💡 Future Enhancements

Planned features:
- [ ] Save/load investigation sessions
- [ ] Real-time collaboration
- [ ] More visualization layouts (hierarchical, radial)
- [ ] Timeline view of investigations
- [ ] Report generation (PDF/HTML)
- [ ] Graph filtering and search
- [ ] Custom node types and relationships

## 🤝 Support

For issues or questions:
- GitHub Issues: https://github.com/fr4nc1stein/osint-framework/issues
- Documentation: https://osif.laet4x.com/
