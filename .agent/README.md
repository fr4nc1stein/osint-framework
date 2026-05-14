# .agent/ Directory

**Purpose:** Documentation and planning resources for AI coding agents and developers working on the OSIF project.

**Status:** This directory is gitignored and contains internal development documentation.

---

## 📁 **Contents**

### **[architecture.md](./architecture.md)**
Complete technical architecture documentation including:
- System architecture overview
- Component breakdown (CLI, Web, Modules)
- Data flow diagrams
- Technology stack details
- Security considerations
- Deployment architecture
- Performance characteristics
- Scalability considerations

**Use this when:** Understanding how the system works, planning major changes, or onboarding new developers.

---

### **[feature-planning.md](./feature-planning.md)**
Feature roadmap and planning documentation including:
- Current status and completed features
- Phased roadmap (Phases 1-4)
- Priority matrix
- UI/UX improvements backlog
- Technical debt tracking
- Success criteria
- Decision log

**Use this when:** Planning new features, prioritizing work, or reviewing project progress.

---

### **[development-guide.md](./development-guide.md)**
Practical development guide including:
- Getting started instructions
- Project structure
- Development workflow
- Coding standards (Python, JavaScript)
- Module development templates
- Testing guidelines
- Debugging tips
- Contributing guidelines

**Use this when:** Writing code, creating new modules, or contributing to the project.

---

## 🤖 **For AI Coding Agents**

### **Quick Start**
1. Read `architecture.md` to understand the system
2. Check `feature-planning.md` for current priorities
3. Follow `development-guide.md` for coding standards
4. Implement features according to the roadmap

### **Best Practices**
- Always check existing documentation before making architectural decisions
- Update relevant `.md` files when making significant changes
- Follow the coding standards in `development-guide.md`
- Reference the priority matrix in `feature-planning.md` for task selection
- Document new features in the appropriate files

### **Common Tasks**

**Adding a New Module:**
1. Check `architecture.md` → Module System section
2. Follow template in `development-guide.md` → Module Development
3. Update `feature-planning.md` if it's a planned feature

**Adding a New API Integration:**
1. Check `architecture.md` → External Integrations
2. Follow API key management in `development-guide.md`
3. Update `.env.example` and `README.md`

**Implementing a Roadmap Feature:**
1. Find feature in `feature-planning.md` → Roadmap
2. Check dependencies and effort estimate
3. Follow development workflow in `development-guide.md`
4. Update feature status when complete

---

## 📝 **Suggested Additional Files**

You can add more documentation files to this directory as needed:

### **api-design.md**
- API endpoint specifications
- Request/response schemas
- Authentication flows
- Error handling patterns

### **database-schema.md**
- Database design (when implemented)
- Entity relationships
- Migration strategy
- Indexing strategy

### **testing-strategy.md**
- Test coverage goals
- Testing frameworks
- CI/CD pipeline
- Quality gates

### **security-guidelines.md**
- Security best practices
- Vulnerability management
- Penetration testing results
- Security audit checklist

### **deployment-guide.md**
- Production deployment steps
- Environment configuration
- Monitoring setup
- Backup strategy

### **module-catalog.md**
- Complete list of all modules
- Module capabilities
- API requirements
- Usage examples

### **changelog.md**
- Version history
- Breaking changes
- Migration guides
- Release notes

---

## 🔄 **Maintenance**

### **Keep Documentation Updated**
- Update `architecture.md` when system design changes
- Update `feature-planning.md` when priorities shift
- Update `development-guide.md` when standards change
- Add decision rationale to `feature-planning.md` → Decision Log

### **Review Cycle**
- Weekly: Review feature priorities
- Monthly: Update roadmap progress
- Quarterly: Architectural review
- Per release: Update all documentation

---

## 🎯 **Documentation Philosophy**

**Why This Directory Exists:**
- Provides context for AI coding agents
- Maintains institutional knowledge
- Ensures consistency across development
- Speeds up onboarding
- Documents architectural decisions

**What Belongs Here:**
- Technical architecture
- Development processes
- Planning documents
- Internal guidelines
- Decision rationale

**What Doesn't Belong Here:**
- User-facing documentation (goes in `/docs/` or `README.md`)
- API keys or secrets (goes in `.env`)
- Generated files
- Temporary notes
- Code files

---

## 📚 **Related Documentation**

**In Repository Root:**
- `README.md` - User-facing project documentation
- `WEB_INTERFACE_GUIDE.md` - Web UI usage guide
- `.env.example` - Configuration template

**External Resources:**
- [GitHub Repository](https://github.com/fr4nc1stein/osint-framework)
- [OSINT Framework](https://osintframework.com/)
- [sploitkit Documentation](https://github.com/dhondta/python-sploitkit)

---

## 💡 **Tips for AI Agents**

1. **Always read before writing** - Check existing docs before making changes
2. **Be consistent** - Follow established patterns and conventions
3. **Document decisions** - Add rationale to decision log
4. **Update incrementally** - Keep docs in sync with code changes
5. **Think holistically** - Consider impact on entire system

---

**Last Updated:** 2026-05-13  
**Maintained By:** Project contributors and AI coding agents
