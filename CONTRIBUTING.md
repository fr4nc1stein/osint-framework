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

- Python 3.12 or higher
- Git
- Virtual environment support

### Setup Steps

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/osint-framework.git
cd osint-framework

# 2. Activate virtual environment
source bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Test the installation
./osif --help
python3 web_server.py
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

### Creating a New Module

Modules are organized by category in the `modules/` directory:

```
modules/
├── attack-surface/
├── blockchain/
├── email/
├── geolocation/
├── host_enum/
├── ioc/
├── mobile/
├── source-code/
└── web_enum/
```

### Module Template

```python
from sploitkit import *
from dotenv import load_dotenv
from terminaltables import SingleTable
import os
import requests

class YourModuleName(Module):
    """Brief description of what this module does
    
    Author:  your-name
    Version: 1.0
    """
    load_dotenv()
    API_KEY = os.getenv('YOUR_API_KEY')

    config = Config({
        Option(
            'TARGET',
            "Description of target parameter",
            True,  # Required
        ): str("default-value"),
    })    

    def run(self):
        """Main execution logic"""
        if not self.API_KEY:
            self.logger.error("API key not configured")
            return

        target = self.config.option('TARGET').value
        
        try:
            results = self.investigate(target)
            self.display_results(results)
        except Exception as e:
            self.logger.error(f"Error: {e}")
    
    def investigate(self, target: str) -> dict:
        """Perform the investigation"""
        # Implementation
        pass
    
    def display_results(self, results: dict):
        """Display results in formatted table"""
        table_data = [
            ("Field", "Value"),
            ("Target", results.get("target")),
        ]
        table = SingleTable(table_data, "Results")
        print("\n" + table.table)
```

### Module Checklist

- [ ] Inherits from `Module` class
- [ ] Has descriptive docstring
- [ ] Validates API keys (if required)
- [ ] Handles errors gracefully
- [ ] Displays results in formatted table
- [ ] Follows naming conventions
- [ ] Added to appropriate category folder

---

## 🧪 Testing

### Manual Testing

```bash
# Test CLI module
./osif
use category/module_name
show options
set TARGET value
run

# Test web server
python3 web_server.py
# Open http://localhost:5001 and test
```

### Writing Tests (Future)

When the test framework is implemented:

```python
# tests/test_your_module.py
import pytest
from modules.category.your_module import YourModuleName

def test_module_loads():
    module = YourModuleName()
    assert module is not None

def test_module_requires_api_key():
    # Test implementation
    pass
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