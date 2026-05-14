# OSIF Development Guide

**Project:** OSIF (Open Source Intelligence Framework)  
**Last Updated:** 2026-05-13

---

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.12+ (3.13 recommended)
- Git
- Virtual environment support
- API keys for external services (optional)

### **Initial Setup**

```bash
# Clone repository
git clone https://github.com/fr4nc1stein/osint-framework.git
cd osint-framework

# Activate virtual environment
source bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Test installation
./osif --help
```

---

## 📁 **Project Structure**

```
osint-framework/
├── .agent/                    # Agent documentation (gitignored)
│   ├── architecture.md        # System architecture
│   ├── feature-planning.md    # Roadmap & features
│   └── development-guide.md   # This file
├── modules/                   # OSINT modules (gitignored)
│   ├── attack-surface/
│   ├── blockchain/
│   ├── email/
│   ├── geolocation/
│   ├── host_enum/
│   ├── ioc/
│   │   ├── abusech.py
│   │   ├── abuseipdb.py
│   │   └── virustotal.py
│   ├── mobile/
│   ├── source-code/
│   └── web_enum/
├── static/                    # Web UI assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       └── graph.js
├── templates/                 # HTML templates
│   └── index.html
├── web/                       # Legacy web app
│   └── app.py
├── .env                       # Environment config (gitignored)
├── .env.example               # Example config
├── .gitignore                 # Git ignore rules
├── osif                       # Main CLI script
├── web_server.py              # Web interface server
├── start_web.sh               # Quick start script
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
└── WEB_INTERFACE_GUIDE.md     # Web UI guide
```

---

## 🔧 **Development Workflow**

### **1. Create a New Branch**

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Or bug fix branch
git checkout -b fix/bug-description
```

### **2. Make Changes**

Follow the coding standards below and test your changes.

### **3. Commit Changes**

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add new feature description"
# or
git commit -m "fix: resolve bug description"
```

**Commit Message Format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### **4. Push and Create PR**

```bash
# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
```

---

## 🎨 **Coding Standards**

### **Python Style**

**Follow PEP 8:**
```python
# Good
def investigate_domain(domain: str) -> dict:
    """Investigate a domain and return results.
    
    Args:
        domain: Domain name to investigate
        
    Returns:
        Dictionary containing investigation results
    """
    results = {}
    # Implementation
    return results

# Bad
def InvestigateDomain(domain):
    results={}
    return results
```

**Type Hints:**
```python
# Always use type hints
def add_node(node_id: str, label: str, node_type: str, data: dict = None) -> dict:
    pass
```

**Docstrings:**
```python
def complex_function(param1: str, param2: int) -> bool:
    """Short description of function.
    
    Longer description if needed. Explain what the function does,
    any side effects, and important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

### **Module Development**

**Template for New Module:**
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
        Option(
            'OPTIONAL_PARAM',
            "Description of optional parameter",
            False,  # Not required
        ): int(100),
    })    

    def run(self):
        """Main execution logic"""
        # Validate API key
        if not self.API_KEY:
            self.logger.error("API key not configured in .env file")
            return

        # Get parameters
        target = self.config.option('TARGET').value
        
        try:
            # Your investigation logic here
            results = self.investigate(target)
            
            # Display results in table
            self.display_results(results)
            
        except Exception as e:
            self.logger.error(f"Error: {e}")
    
    def investigate(self, target: str) -> dict:
        """Perform the actual investigation"""
        # Implementation
        pass
    
    def display_results(self, results: dict):
        """Display results in formatted table"""
        table_data = [
            ("Field", "Value"),
            ("Target", results.get("target")),
            # Add more fields
        ]
        table = SingleTable(table_data, "Results")
        print("\n" + table.table)
```

### **Web API Development**

**Endpoint Template:**
```python
@app.route('/api/investigate/newtype', methods=['POST'])
def investigate_newtype():
    """Investigate a new type of entity"""
    data = request.json
    target = data.get('target')
    
    # Validation
    if not target:
        return jsonify({"error": "Target is required"}), 400
    
    # Create node
    node_id = f"newtype_{target}"
    add_node(node_id, target, "newtype", {"value": target})
    
    results = {"nodes": [], "edges": []}
    
    try:
        # Investigation logic
        # ...
        
        results["status"] = "success"
        results["target"] = target
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(results)
```

### **JavaScript Style**

```javascript
// Use modern ES6+ syntax
const investigateDomain = async (domain) => {
    try {
        const response = await fetch('/api/investigate/domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ domain }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Investigation failed:', error);
        throw error;
    }
};

// Use const/let, not var
const API_BASE = '/api';
let currentGraph = null;

// Use arrow functions
const updateGraph = (newData) => {
    // Implementation
};
```

---

## 🧪 **Testing**

### **Manual Testing**

```bash
# Test CLI
./osif
use ioc/abuseipdb
set IP 8.8.8.8
run

# Test web server
python3 web_server.py
# Open http://localhost:5001
```

### **Unit Tests** (Future)

```python
# tests/test_modules.py
import pytest
from modules.ioc.abuseipdb import AbuseIPDBCheck

def test_abuseipdb_module_loads():
    module = AbuseIPDBCheck()
    assert module is not None

def test_abuseipdb_requires_api_key():
    # Test implementation
    pass
```

---

## 🐛 **Debugging**

### **CLI Debugging**

```bash
# Enable verbose mode
./osif -v

# Check module loading
./osif
show modules
show issues
```

### **Web Server Debugging**

```python
# In web_server.py, Flask debug mode is enabled
# Check terminal output for errors

# Add debug prints
print(f"[DEBUG] Investigating: {domain}")
```

### **Common Issues**

**1. Module Not Loading**
- Check file is in correct `modules/` subdirectory
- Ensure class inherits from `Module`
- Check for syntax errors

**2. API Key Not Working**
- Verify `.env` file exists
- Check key name matches exactly
- Ensure `load_dotenv()` is called

**3. Port Already in Use**
- System auto-increments to next port
- Or manually specify: `python3 web_server.py --port 5002`

**4. Import Errors**
- Activate virtual environment: `source bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

---

## 📦 **Adding Dependencies**

```bash
# Install new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Or manually add to requirements.txt
echo "package-name>=1.0.0" >> requirements.txt
```

---

## 🔐 **API Key Management**

### **Adding New API Integration**

1. **Update `.env.example`:**
```bash
# Add new key
NEW_SERVICE_API_KEY=""
```

2. **Update README.md:**
```markdown
1. NEW SERVICE API https://newservice.com/api
```

3. **Load in module:**
```python
load_dotenv()
NEW_SERVICE_API_KEY = os.getenv('NEW_SERVICE_API_KEY')
```

---

## 🚢 **Deployment**

### **Development Server**

```bash
# Start web server
./start_web.sh

# Or manually
python3 web_server.py
```

### **Production** (Future)

```bash
# Use Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 web_server:app

# Or uWSGI
uwsgi --http :5001 --wsgi-file web_server.py --callable app
```

---

## 📝 **Documentation**

### **Update Documentation When:**
- Adding new features
- Changing API endpoints
- Modifying configuration
- Adding dependencies
- Changing architecture

### **Documentation Files:**
- `README.md` - User-facing documentation
- `WEB_INTERFACE_GUIDE.md` - Web UI guide
- `.agent/architecture.md` - Technical architecture
- `.agent/feature-planning.md` - Roadmap
- `.agent/development-guide.md` - This file

---

## 🤝 **Contributing Guidelines**

### **Before Submitting PR:**

- [ ] Code follows style guidelines
- [ ] All tests pass (when implemented)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No sensitive data in commits
- [ ] `.env` not committed
- [ ] Branch is up to date with main

### **PR Template:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
```

---

## 🎯 **Best Practices**

### **Security**
- Never commit API keys
- Validate all user input
- Use environment variables for secrets
- Implement rate limiting
- Add authentication before production

### **Performance**
- Use async for I/O operations
- Cache API responses
- Limit graph node count
- Optimize database queries
- Monitor API rate limits

### **Code Quality**
- Write self-documenting code
- Add comments for complex logic
- Keep functions small and focused
- Use meaningful variable names
- Handle errors gracefully

### **Git**
- Commit often
- Write clear commit messages
- Keep commits atomic
- Don't commit generated files
- Use `.gitignore` properly

---

## 📚 **Resources**

### **Python**
- [PEP 8 Style Guide](https://pep8.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Flask Documentation](https://flask.palletsprojects.com/)

### **JavaScript**
- [MDN Web Docs](https://developer.mozilla.org/)
- [vis.js Documentation](https://visjs.github.io/vis-network/docs/network/)

### **OSINT**
- [OSINT Framework](https://osintframework.com/)
- [Awesome OSINT](https://github.com/jivoi/awesome-osint)
- [Bellingcat Toolkit](https://docs.google.com/spreadsheets/d/18rtqh8EG2q1xBo2cLNyhIDuK9jrPGwYr9DI2UncoqJQ/)

### **Tools**
- [sploitkit Documentation](https://github.com/dhondta/python-sploitkit)
- [Requests Documentation](https://requests.readthedocs.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

## 💡 **Tips & Tricks**

### **Fast Module Development**
```bash
# Copy existing module as template
cp modules/ioc/abuseipdb.py modules/ioc/newmodule.py

# Edit and test
./osif
use ioc/newmodule
show options
```

### **Quick API Testing**
```bash
# Test endpoint with curl
curl -X POST http://localhost:5001/api/investigate/domain \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com"}'
```

### **Graph Debugging**
```javascript
// In browser console
console.log(graphData);  // View current graph
network.fit();           // Reset view
```

---

## 🆘 **Getting Help**

- Check existing issues on GitHub
- Read documentation thoroughly
- Search Stack Overflow
- Ask in project discussions
- Contact maintainers

---

## 📄 **License**

AGPL v3 - See LICENSE.md for details
