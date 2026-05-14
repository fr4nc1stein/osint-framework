# OSIF v2.0.0 - Web Interface & Enhanced Features 🎉

We're excited to announce OSIF v2.0.0, a major release that transforms OSIF into a dual-interface OSINT platform with a brand new web-based graph visualization system!

## 🌟 Highlights

### 🌐 Web Graph Visualization
The biggest addition in v2.0.0 is the **interactive web interface** featuring Maltego-style graph visualization:

- **Visual Investigation**: Interactive node-edge graph for exploring relationships
- **Real-time Updates**: Watch your investigation graph grow as entities are discovered
- **Multiple Entry Points**: Investigate domains, IPs, emails, and Bitcoin addresses
- **Smart Interactions**: Click nodes for details, double-click to investigate further
- **Export Capabilities**: Save your investigation graphs as JSON

![Web Graph Visualization](screenshots/web_graph.png)

### 🛡️ IP Reputation Intelligence
New **AbuseIPDB integration** provides comprehensive IP threat intelligence:

- Abuse confidence scoring (0-100%)
- Threat level classification (Low/Medium/High Risk)
- Recent abuse report history
- Visual threat indicators in graph
- Available in both CLI and web interface

### 🔧 Smart Port Management
Intelligent port conflict detection and resolution:

- Automatically detects when port 5001 is in use
- Auto-increments to next available port (5001-5005)
- Clear error messages showing which ports are occupied
- Manual port selection via `--port` flag

### 📚 Comprehensive Documentation
1,819 lines of developer documentation added:

- **Architecture Guide** - Complete system design and technical details
- **Feature Planning** - Roadmap, priorities, and backlog
- **Development Guide** - Coding standards, workflows, best practices
- **Contributing Guide** - Professional contribution guidelines

## 🚀 Getting Started

### Quick Start - Web Interface

```bash
git clone https://github.com/fr4nc1stein/osint-framework.git
cd osint-framework
source bin/activate
pip install -r requirements.txt
./start_web.sh
```

Then open http://localhost:5001 in your browser!

### CLI with Web Server

```bash
./osif  # Web server starts automatically in background
```

### CLI Only

```bash
./osif --no-web
```

## 📦 What's New

### Investigation Capabilities

**Domain Investigation:**
- Email discovery via Tomba
- DNS records (A, MX)
- Subdomain enumeration via Certificate Transparency (crt.sh)
- Automatic IP resolution for discovered hosts

**IP Investigation:**
- Geolocation and ISP information (ip-api.com)
- Reputation checking (AbuseIPDB)
- Port scanning (Shodan)
- Hostname discovery
- Threat level indicators

**Email Investigation:**
- Domain extraction and linking
- Prepared for Have I Been Pwned integration

**Bitcoin Investigation:**
- Wallet balance checking
- Transaction history via blockchain.info

### Technical Improvements

- **Flask REST API** with CORS support
- **vis.js** for interactive graph rendering
- **Background server management** in CLI
- **Enhanced error handling** and validation
- **Modern responsive UI** design

## 📊 By the Numbers

- **5,548+ lines** of new code and documentation
- **19 new files** added
- **2,543 lines** of documentation
- **3,005+ lines** of code
- **4 comprehensive** developer guides

## 🔗 New Integrations

- **AbuseIPDB** - IP reputation and threat intelligence
- **crt.sh** - Certificate Transparency for subdomain discovery
- **ip-api.com** - IP geolocation services
- **Enhanced Tomba** - Email discovery and verification

## 🛠️ Breaking Changes

None! The CLI interface remains fully backward compatible. The web interface is an addition, not a replacement.

## 📝 Documentation

- **Main Documentation**: https://osif.laet4x.com/
- **Web Interface Guide**: [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md)
- **Architecture**: [.agent/architecture.md](.agent/architecture.md)
- **Development Guide**: [.agent/development-guide.md](.agent/development-guide.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

## 🔜 What's Next (v2.1.0)

We're already planning the next release with exciting features:

- Database persistence for investigations
- Async API calls for 3-5x performance improvement
- GitHub OSINT module
- Reddit OSINT module
- Have I Been Pwned integration
- Enhanced authentication system

See the full roadmap in [.agent/feature-planning.md](.agent/feature-planning.md)

## 🙏 Contributors

Special thanks to everyone who contributed to this release:

- @laet4x - Core development and web interface
- @cadeath - Contributions and testing
- @benemohamed - Tomba integration
- All community contributors and testers

## 💬 Feedback & Support

- **Issues**: [GitHub Issues](https://github.com/fr4nc1stein/osint-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fr4nc1stein/osint-framework/discussions)
- **Documentation**: https://osif.laet4x.com/

## 📄 License

OSIF is licensed under AGPL v3. See [LICENSE.md](LICENSE.md) for details.

---

**Full Changelog**: https://github.com/fr4nc1stein/osint-framework/compare/v1.1.1...v2.0.0

**Download**: [v2.0.0 Release](https://github.com/fr4nc1stein/osint-framework/releases/tag/v2.0.0)
