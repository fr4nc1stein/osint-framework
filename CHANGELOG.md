# Changelog

All notable changes to OSIF (Open Source Intelligence Framework) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-05-13

### 🎉 Major Release - Web Interface & Enhanced Features

This is a major release introducing a completely new web-based graph visualization interface alongside the traditional CLI, transforming OSIF into a dual-interface OSINT platform.

### ✨ Added

#### Web Graph Visualization
- **Interactive Graph Interface**: Maltego-style web visualization for OSINT investigations
- **Real-time Entity Linking**: Automatic discovery and linking of related entities
- **Multiple Entry Points**: Support for domain, IP, email, and Bitcoin address investigations
- **Node Interaction**: Click to view details, double-click to investigate further
- **Export Capabilities**: Export investigation graphs as JSON
- **Modern UI**: Responsive design with vis.js graph rendering
- **Background Server Management**: Automatic web server startup with CLI

#### Intelligence Gathering
- **AbuseIPDB Integration**: IP reputation checking with abuse confidence scores
  - Threat level classification (Low/Medium/High Risk)
  - Recent abuse report history
  - CLI module (`modules/ioc/abuseipdb.py`)
  - Web integration with automatic threat node creation
- **Certificate Transparency**: Subdomain discovery via crt.sh integration
- **Enhanced Domain Investigation**: Email discovery, DNS records, subdomain enumeration
- **IP Geolocation**: Integration with ip-api.com for location data
- **Email Discovery**: Tomba integration for comprehensive email finding

#### Developer Experience
- **Comprehensive Documentation**: 1,819 lines of developer documentation
  - `.agent/architecture.md` - Complete system architecture (503 lines)
  - `.agent/feature-planning.md` - Roadmap and priorities (496 lines)
  - `.agent/development-guide.md` - Coding standards and workflows (616 lines)
  - `.agent/README.md` - Documentation overview (204 lines)
- **Contributing Guide**: Professional 417-line contribution guidelines
- **Improved README**: Enhanced header with badges, navigation, and structure

#### Infrastructure
- **Smart Port Management**: Automatic port conflict detection and increment (5001-5005)
  - Clear error messages showing which ports are in use
  - Auto-increment to next available port
  - Manual port selection via `--port` flag
- **Web Server**: Flask-based REST API with CORS support
- **Quick Start Script**: `start_web.sh` for easy web interface launch

### 🔧 Changed

- **README.md**: Complete header redesign with centered layout, additional badges, and navigation
- **Module System**: Enhanced with better error handling and API key validation
- **CLI Interface**: Now includes background web server management
- **Configuration**: Enhanced `.env.example` with AbuseIPDB and additional API keys

### 📦 Dependencies

#### New Dependencies
- `flask>=2.3.0` - Web framework
- `flask-cors>=4.0.0` - CORS support
- `requests>=2.31.0` - HTTP client (version bump)

### 🗂️ File Structure

#### New Files
- `web_server.py` - Flask-based graph visualization server (505 lines)
- `static/js/graph.js` - Interactive graph rendering (782 lines)
- `static/js/app.js` - Frontend application logic (558 lines)
- `static/css/style.css` - Modern UI styling (387 lines)
- `templates/index.html` - Main web interface (105 lines)
- `modules/ioc/abuseipdb.py` - AbuseIPDB CLI module (107 lines)
- `WEB_INTERFACE_GUIDE.md` - Comprehensive web UI guide (307 lines)
- `start_web.sh` - Quick start script (53 lines)
- `CHANGELOG.md` - This file
- `.agent/` directory - Developer documentation (4 files)
- `screenshots/web_graph.png` - Web interface screenshot

### 📊 Statistics

- **Total Lines Added**: 5,548+
- **New Files**: 19
- **Documentation**: 2,543 lines
- **Code**: 3,005+ lines

### 🔗 API Integrations

#### New Integrations
- AbuseIPDB (IP reputation)
- crt.sh (Certificate Transparency)
- ip-api.com (IP geolocation)

#### Enhanced Integrations
- Tomba (email discovery)
- DNS resolution (A, MX records)
- Blockchain.info (Bitcoin data)

### 🎯 Investigation Capabilities

#### Domain Investigation
- Email discovery (Tomba)
- DNS records (A, MX)
- Subdomain enumeration (Certificate Transparency)
- Automatic IP resolution for discovered hosts

#### IP Investigation
- Geolocation and ISP information
- Reputation checking (AbuseIPDB)
- Port scanning (Shodan)
- Hostname discovery
- Threat level indicators

#### Email Investigation
- Domain extraction and linking
- Breach checking preparation (HIBP ready)

#### Bitcoin Investigation
- Wallet balance checking
- Transaction history

### 🚀 Usage

#### Web Interface
```bash
./start_web.sh
# or
python3 web_server.py
# Then open http://localhost:5001
```

#### CLI with Web Server
```bash
./osif  # Web server starts automatically
```

#### CLI without Web Server
```bash
./osif --no-web
```

### 📝 Documentation

- Full documentation: https://osif.laet4x.com/
- Web Interface Guide: `WEB_INTERFACE_GUIDE.md`
- Architecture: `.agent/architecture.md`
- Development Guide: `.agent/development-guide.md`
- Contributing: `CONTRIBUTING.md`

### 🙏 Contributors

Special thanks to all contributors who made this release possible:
- @laet4x - Core development
- @cadeath - Contributions
- @benemohamed - Tomba integration
- Community contributors

### 🔜 What's Next (v2.1.0)

Planned features for the next release:
- Database persistence for investigations
- Async API calls for better performance
- GitHub OSINT module
- Reddit OSINT module
- Have I Been Pwned integration
- Enhanced authentication system

---

## [1.1.1] - Previous Release

### Changed
- Various bug fixes and improvements
- Module enhancements

---

## [1.1.0] - Previous Release

### Added
- Initial module system
- Basic CLI interface
- Core OSINT capabilities

---

## [1.0.0] - Initial Release

### Added
- Metasploit-style CLI interface
- Basic OSINT modules
- API integrations (VirusTotal, Shodan, etc.)

---

[2.0.0]: https://github.com/fr4nc1stein/osint-framework/compare/v1.1.1...v2.0.0
[1.1.1]: https://github.com/fr4nc1stein/osint-framework/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/fr4nc1stein/osint-framework/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/fr4nc1stein/osint-framework/releases/tag/v1.0.0
