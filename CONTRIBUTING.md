# Contributing to OSIF

Thank you for your interest in contributing to OSIF (Open Source Intelligence Framework)! We welcome contributions from the community.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Module Development](#module-development)
- [Testing](#testing)
- [Documentation](#documentation)

---

## 🤝 Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

---

## 💡 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List any similar features** in other tools

### Pull Requests

We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests
3. Ensure the test suite passes
4. Make sure your code follows our coding standards
5. Issue that pull request!

---

## 🛠️ Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend-only development)
- Python 3.12+ (for backend-only development)
- Git

### Full Stack (Recommended)

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/osint-framework.git
cd osint-framework
git checkout feature/v2

# 2. Configure environment
cp backend/.env.example .env
# Edit .env and set POSTGRES_PASSWORD, REDIS_PASSWORD, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD

# 3. Start the full stack (migrations run automatically)
docker-compose -f docker-compose.dev.yml up -d --build

# 4. Open the UI
open http://localhost:3000
# API docs: http://localhost:6000/api/docs
```

### Backend-Only (Local)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env

# Start supporting services
docker-compose -f ../docker-compose.dev.yml up -d postgres redis minio minio-init

# Run migrations
alembic upgrade head

# Start API server with reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 6000
```

### Frontend-Only (Local)

```bash
cd frontend
npm install
# Ensure backend is running at localhost:6000
npm run dev   # http://localhost:5173
```

### CLI Console

```bash
# Attach to the running console container
docker exec -it osif_console ./osif

# Or build and run standalone
docker-compose -f docker-compose.dev.yml run --rm console ./osif
```

### Developer Documentation

For detailed development information, see:

- [Architecture Guide](.agent/architecture.md)
- [Development Guide](.agent/development-guide.md)
- [Feature Planning](.agent/feature-planning.md)

---

## 📝 Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Maximum line length: 88 characters (Black formatter)
- Use meaningful variable and function names

**Example:**

```python
def investigate_domain(domain: str, max_results: int = 10) -> dict:
    """Investigate a domain and return results.
    
    Args:
        domain: Domain name to investigate
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary containing investigation results
    """
    results = {}
    # Implementation
    return results
```

### JavaScript Style

- Use modern ES6+ syntax
- Use `const` and `let`, never `var`
- Use arrow functions where appropriate
- Add JSDoc comments for functions

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

**Examples:**

```
feat: add GitHub OSINT module for user reconnaissance
fix: resolve port conflict detection issue
docs: update API documentation for domain investigation
```

---

## 🔄 Submitting Changes

### Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow coding standards
   - Add tests if applicable

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template

### Pull Request Guidelines

**Before submitting:**

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Tests added/updated
- [ ] All tests pass

**PR Description should include:**

- Summary of changes
- Related issue number (if applicable)
- Type of change (bug fix, new feature, etc.)
- Testing performed
- Screenshots (if UI changes)

---

## 🔧 Module Development

### Creating a New OSINT Module (v2)

Backend OSINT modules live in `backend/app/modules/<category>/`.

Categories: `domain`, `ip`, `email`, `username`, `phone`, `bitcoin`

### Module Template

```python
from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module

@register_module
class YourModule(BaseOSINTModule):
    MODULE_ID = "your_module"
    DISPLAY_NAME = "Your Module"
    DESCRIPTION = "What this module does"
    CATEGORY = "domain"          # or ip, email, username, phone, bitcoin
    ACCEPTS = ["domain"]         # seed_kind values this module handles

    async def execute(self, target: str, kind: str, **kwargs) -> list[dict]:
        api_key = await self.get_credential("YOUR_API_KEY_NAME")
        if not api_key:
            return []

        results = []
        # ... call external API, build indicator dicts ...
        return results
```

The module auto-registers on backend startup. Results are written to `scan_results` and appear in the case graph.

### Credential Access

Integration credentials are stored encrypted in PostgreSQL. Use `self.get_credential("PROVIDER_NAME")` — it falls back to the `.env` file if no DB record exists.

### Module Checklist

- [ ] Inherits from `BaseOSINTModule`
- [ ] `MODULE_ID` is unique and snake_case
- [ ] `ACCEPTS` list is accurate
- [ ] Returns `[]` (not raises) when credential is missing
- [ ] Returns `[]` (not raises) on API error
- [ ] Result dicts follow the indicator schema (`type`, `value`, `metadata`)
- [ ] Registered in the correct category folder

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=app tests/

# Specific file
pytest tests/unit/test_modules.py
```

### Manual API Testing

```bash
# Health check
curl http://localhost:6000/health

# List modules
curl http://localhost:6000/api/v1/modules | jq '[.[] | .module_id]'

# Create a case and run a scan
curl -X POST http://localhost:6000/api/v1/cases \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "description": "dev test"}'
```

### Frontend Dev

```bash
cd frontend
npm run lint
npm run type-check
```

---

## 📚 Documentation

### What to Document

- **Code**: Add docstrings to all functions and classes
- **Modules**: Update module list in README.md
- **API Changes**: Update API documentation
- **New Features**: Add to feature-planning.md
- **Architecture Changes**: Update architecture.md

### Documentation Files

- `README.md` - User-facing documentation
- `WEB_INTERFACE_GUIDE.md` - Web UI usage guide
- `.agent/architecture.md` - Technical architecture
- `.agent/development-guide.md` - Development guide
- `.agent/feature-planning.md` - Roadmap and features

---

## 🎯 Good First Issues

Looking for a place to start? Check out issues labeled:

- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements
- `enhancement` - New features

### Suggested Contributions

**Easy:**
- Add new API integrations
- Improve documentation
- Fix typos and formatting
- Add examples

**Medium:**
- Create new OSINT modules
- Enhance web UI
- Add tests
- Improve error handling

**Advanced:**
- Database integration
- Performance optimization
- Security enhancements
- Advanced features

---

## 🔐 Security

If you discover a security vulnerability, please email the maintainers directly instead of creating a public issue.

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the AGPL v3 License.

---

## 🙏 Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- Project documentation

---

## 💬 Questions?

- Check the [documentation](https://osif.laet4x.com/)
- Read the [development guide](.agent/development-guide.md)
- Open a [discussion](https://github.com/fr4nc1stein/osint-framework/discussions)
- Join our community

---

**Thank you for contributing to OSIF! 🎉**