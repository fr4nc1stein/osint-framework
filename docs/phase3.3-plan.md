# OSIF v2.0 - Phase 3.3 Plan: Integration Marketplace, OSINT Bot Tiers, and Next Best Features

**Date:** 2026-07-02  
**Status:** Planning  
**Focus:** Decide the next highest-value features after Phase 3.2 and define an OSINT integration strategy grouped by free, freemium, paid, commercial, and restricted-access providers.

---

## Summary

After Phase 3.2, the next best work is not just "add more APIs." OSIF needs a structured integration marketplace, provider tiering, stronger evidence handling, and a clear path for Community, Pro, and Enterprise workflows.

The recommended direction is:

- Build an integration catalog that knows each provider's access tier, required credentials, data category, rate limits, legal sensitivity, and supported module types.
- Fix existing provider assumptions before adding many new ones.
- Add high-value free/community feeds first, because they improve investigation coverage without forcing users to buy tools.
- Add paid/commercial integrations behind a clear "bring your own key" model.
- Add restricted/special-access integrations only after audit logging, RBAC, and compliance controls exist.
- Package the "OSINT bot" experience around workflows, not raw providers.

---

## Current OSIF Integration Baseline

### Existing Modules

Current module coverage:

- DNS records
- WHOIS lookup
- subdomain enumeration
- email domain extraction
- IP geolocation
- AbuseIPDB IP reputation
- Shodan IP host enrichment
- Tomba domain email discovery
- VirusTotal domain reputation
- HIBP breach lookup
- urlscan domain/URL lookup

### Existing Integration Catalog

Current integration catalog includes:

- Shodan
- VirusTotal
- AbuseIPDB
- Tomba
- HIBP
- Hunter
- IPinfo
- AlienVault OTX
- Censys
- URLScan.io

### Immediate Corrections

Before adding new integrations:

- Correct HIBP handling:
  - HIBP email breach and paste lookups require a subscription key.
  - HIBP Pwned Passwords range API is free and does not require a subscription key.
- Treat urlscan as "free with account/API key for useful quotas and private/unlisted scan options," not purely no-key.
- Replace hard-coded provider status with the Phase 3.2 database-backed credential model.
- Add provider-specific rate limit metadata to the integration catalog.
- Add provider-specific data handling warnings, especially for URL submission, breach data, and AI enrichment.

---

## Best Next Features

### 1. Integration Marketplace

Build `/integrations` into a real marketplace-style admin surface.

Features:

- Provider grouping by access tier:
  - Free/no key
  - Free account or free API key
  - Free tier plus paid upgrades
  - Paid/commercial
  - Restricted/special access
- Provider grouping by OSINT category:
  - domain
  - IP/network
  - URL/phishing/malware
  - email/breach
  - threat intelligence
  - infrastructure search
  - people/company enrichment
  - vulnerability/exploitation intelligence
- Provider cards with:
  - configured status
  - credential source: DB, `.env`, missing
  - enabled/disabled toggle
  - test connection
  - last success/failure
  - rate limit profile
  - data sensitivity badge
  - terms/commercial use note

Why this is next:

- It makes integrations manageable before provider count grows.
- It avoids a messy settings page full of unrelated API keys.
- It gives the user a clean path to "free only" or "paid/commercial" deployments.

### 2. OSINT Bot Workflow Builder

Instead of only running modules manually, add saved investigation workflows.

Examples:

- Domain reconnaissance bot
- IP reputation bot
- Phishing URL triage bot
- Email exposure bot
- Company footprint bot
- Infrastructure attribution bot
- Executive summary bot

Each workflow should define:

- accepted input kinds
- modules to run
- required integrations
- optional integrations
- cost tier
- estimated runtime
- output sections
- report template
- risk/compliance warnings

Why this is high value:

- Users think in investigations, not modules.
- It makes the paid/free provider split understandable.
- It gives OSIF a product-level experience without hiding the underlying evidence.

### 3. Evidence-Centered Findings

Add a first-class "finding" layer between raw graph edges and reports.

New concept:

```text
Finding
- id
- case_id
- title
- severity
- confidence
- status
- summary
- evidence_refs
- source_modules
- first_seen
- last_seen
- analyst_notes
```

Finding examples:

- "Domain resolves to high-risk IP"
- "Email appears in breach corpus"
- "Host exposes remote administration service"
- "URL observed in phishing feed"
- "IP associated with opportunistic internet scanning"

Why this matters:

- Graphs are good for exploration.
- Reports need curated conclusions.
- Enterprise users need defensible findings with citations.

### 4. Provider-Aware Rate Limiting And Cost Controls

Add a provider budget layer:

- requests per scan
- requests per case
- requests per day
- paid-provider warning before scan
- block expensive modules unless enabled
- estimated credit usage before workflow launch

This matters because many OSINT APIs have different quotas and paid plans. A workflow should not accidentally burn paid credits.

### 5. Integration Health And Coverage Dashboard

Add an admin/operator dashboard:

- configured providers
- failing providers
- last successful call
- current rate limit status
- recent 429/401/403 errors
- which workflows are blocked by missing credentials
- free-only vs paid-enabled coverage score

This helps teams understand why a scan produced weak or missing results.

### 6. Compliance And Data Handling Controls

Add controls before integrating sensitive providers:

- URL submission visibility controls: public, unlisted, private where supported
- "Do not submit target to third party" mode
- breach-data warning and approval gate
- AI redaction rules
- per-case data sensitivity label
- audit log for external enrichment calls

This is important for OSINT because many providers receive the queried indicator.

---

## Integration Access Tiers

### Tier 0: Free / No API Key

Use these for the Community/default experience.

Recommended providers or data sources:

| Provider/Data Source | Category | Use |
|---|---|---|
| DNS resolver | domain | A, AAAA, MX, NS, TXT, CNAME records |
| RDAP / WHOIS where available | domain/IP | registration and ownership metadata |
| Public CT logs | domain | certificate names and passive subdomain leads |
| Pwned Passwords range API | breach/password | safe k-anonymity password hash checks |
| PhishTank public downloads | phishing | verified online phishing URLs |
| OpenPhish Community feed | phishing | limited free phishing URL feed |

Implementation notes:

- Cache aggressively.
- Normalize all feed records into indicators and evidence refs.
- Do not submit private target data unnecessarily.

### Tier 1: Free Account / Free API Key

These require sign-up or an auth key but can be used without a paid plan for limited workflows.

Recommended providers:

| Provider | Category | Use |
|---|---|---|
| urlscan.io | URL/domain | search scans, submit URLs, screenshot/DOM metadata |
| URLhaus | malware URL | malware URL checks and datasets |
| GreyNoise Community | IP reputation | internet scanner/noise context |
| IPinfo Lite | IP/ASN | country-level geo and ASN context |
| AbuseIPDB Individual | IP reputation | IP checks and reports within free quota |

Implementation notes:

- Show "free account required" badge.
- Support provider-specific quotas.
- For urlscan, expose scan visibility and PII warnings.
- For URLhaus, distinguish community/fair-use access from commercial access.

### Tier 2: Free Tier With Paid Upgrades

These should work with a bring-your-own-key model and clear quota/cost warnings.

Recommended providers:

| Provider | Category | Why Add |
|---|---|---|
| AbuseIPDB | IP reputation | strong IP abuse scoring; free and paid request tiers |
| IPinfo | IP/ASN/privacy | useful upgrade path from Lite to Core/Plus/Max |
| Hunter.io | email/company | domain email discovery and verification |
| Tomba | email/company | domain email discovery, verification, company enrichment |
| GreyNoise | IP threat intel | free community lookup, paid enterprise automation |
| urlscan Pro | URL/phishing | private scans, higher quotas, brand/phishing metadata |

Implementation notes:

- Add `plan_tier` and `quota_profile` fields to provider config.
- Add UI warnings when a workflow uses paid-capable APIs.
- Allow disabling paid modules per deployment.

### Tier 3: Paid / Commercial

These are valuable but should not be assumed available.

Recommended providers:

| Provider | Category | Why Add |
|---|---|---|
| VirusTotal Enterprise | threat intel | richer relationships, hunting, graph, file/URL/domain/IP context |
| Censys Platform | internet-wide search | host/certificate/service intelligence |
| SecurityTrails | passive DNS/domain | DNS history, subdomains, WHOIS-style enrichment |
| WhoisXML API | domain/IP/email | WHOIS, reverse WHOIS, DNS, threat intel datasets |
| BuiltWith | technology profiling | web technology stack and company footprinting |
| Criminal IP | threat/intel search | attack surface and IOC enrichment |
| Shodan paid plans | infrastructure search | query credits, host/service details, facets |

Implementation notes:

- Mark these as `commercial`.
- Do not show hard-coded prices in UI; provider pricing changes.
- Show "requires paid subscription or commercial license."
- Require explicit enablement before workflows use them.

### Tier 4: Restricted / Special Access

These should be planned carefully and protected by compliance controls.

Examples:

| Provider Type | Category | Risk |
|---|---|---|
| breach-data providers | breach/identity | sensitive personal data, legal/compliance obligations |
| stealer-log intelligence | credential exposure | high sensitivity; strict access terms |
| law-enforcement feeds | phishing/malware | eligibility restrictions |
| closed threat-intel sharing communities | threat intelligence | redistribution and TLP constraints |
| dark-web intelligence platforms | actor/infrastructure | high cost, high legal/compliance sensitivity |

Implementation rules:

- Do not add these until audit logging and RBAC exist.
- Add data classification labels.
- Add explicit case-level approval before query.
- Add terms-of-use acknowledgement.
- Keep raw sensitive data out of default reports.

---

## Proposed Provider Metadata Model

Add a provider catalog object that can drive backend logic and frontend grouping.

```python
{
    "id": "abuseipdb",
    "name": "AbuseIPDB",
    "category": "ip_reputation",
    "access_tier": "freemium",
    "commercial_use": "allowed_by_plan",
    "credential_type": "api_key",
    "credential_fields": ["api_key"],
    "env_fallback": ["ABUSEIPDB_API_KEY"],
    "supports_test": True,
    "supports_rate_limit_headers": False,
    "default_rate_limit_profile": "abuseipdb_free",
    "data_sensitivity": "medium",
    "submits_target_to_provider": True,
    "supports_private_submission": False,
    "module_ids": ["abuseipdb"],
    "workflow_ids": ["ip_reputation_bot"],
}
```

Recommended `access_tier` values:

- `free_no_key`
- `free_key`
- `freemium`
- `paid`
- `commercial`
- `restricted`

Recommended `data_sensitivity` values:

- `low`
- `medium`
- `high`
- `restricted`

---

## Integration Build Priority

### Priority 1: Fix And Harden Existing Integrations

- HIBP: split email breach lookup from Pwned Passwords.
- urlscan: add API key support, visibility controls, and result polling.
- AbuseIPDB: keep current module, add DB-backed credential provider and health test.
- Shodan: add credential test and query-credit warnings.
- VirusTotal: support DB credentials and clarify public vs enterprise feature scope.
- Tomba/Hunter: decide whether to support both or keep one primary email discovery provider.

### Priority 2: Add High-Value Free/Community Feeds

- URLhaus malware URL lookup/feed ingest.
- PhishTank verified online phishing feed ingest.
- OpenPhish Community feed ingest.
- Certificate Transparency subdomain enrichment.
- GreyNoise Community IP context.
- IPinfo Lite as optional replacement/enhancement for current geolocation.

### Priority 3: Add Freemium/Paid Providers

- Hunter.io
- IPinfo paid tiers
- GreyNoise paid API
- Censys Platform
- SecurityTrails
- WhoisXML API

### Priority 4: Add Enterprise/Restricted Providers

Only after auth, RBAC, audit logging, and case data classification:

- breach-data providers
- stealer-log intelligence
- dark-web intelligence
- closed sharing communities
- law-enforcement/government-only feeds

---

## Workflow Roadmap

### Domain Recon Bot

Input:

- domain

Free path:

- DNS records
- WHOIS/RDAP
- subdomain enumeration
- CT log enrichment
- urlscan search

Paid/enhanced path:

- SecurityTrails
- Censys
- VirusTotal relationships
- WhoisXML API

Output:

- subdomains
- DNS relationships
- certificates
- related URLs
- hosting/IP summary
- report-ready findings

### IP Reputation Bot

Input:

- IP address

Free path:

- geolocation
- ASN
- AbuseIPDB free tier
- GreyNoise community if configured

Paid/enhanced path:

- Shodan
- IPinfo paid privacy/proxy attributes
- GreyNoise paid intelligence
- VirusTotal IP relationships

Output:

- abuse score
- scanner/noise classification
- open services
- ASN/network ownership
- privacy/proxy/VPN flags

### URL/Phishing Triage Bot

Input:

- URL

Free path:

- urlscan search
- URLhaus lookup
- PhishTank feed match
- OpenPhish feed match

Paid/enhanced path:

- urlscan private scan/Pro metadata
- VirusTotal URL report
- OpenPhish Premium

Output:

- screenshot/DOM references where allowed
- phishing/malware feed matches
- hosting/domain/IP relationships
- brand impersonation if available

### Email Exposure Bot

Input:

- email or domain

Free path:

- email domain extraction
- HIBP Pwned Passwords only for password hashes, not raw passwords

Paid/enhanced path:

- HIBP email breach/paste lookup
- Hunter/Tomba domain discovery
- HIBP verified domain search

Output:

- breach exposure summary
- paste exposure summary
- discovered addresses for owned/authorized domains
- source citations and compliance warning

### Company Footprint Bot

Input:

- organization name or domain

Free path:

- domain recon
- CT logs
- DNS

Paid/enhanced path:

- BuiltWith
- Hunter/Tomba
- SecurityTrails
- Censys
- IPinfo enterprise/company datasets

Output:

- domains
- technologies
- exposed infrastructure
- email patterns
- subsidiaries/related assets where provider data supports it

---

## Data Model Additions

### Integration Catalog

Can start as static JSON or Python constants, but should be structured enough to migrate into DB later.

Fields:

- `id`
- `name`
- `description`
- `category`
- `access_tier`
- `commercial_use`
- `credential_type`
- `credential_fields`
- `env_fallback`
- `data_sensitivity`
- `submits_target_to_provider`
- `supports_private_submission`
- `default_rate_limit_profile`
- `module_ids`
- `workflow_ids`
- `source_url`

### Workflow Template

```text
workflow_templates
- id
- name
- description
- accepted_kinds
- required_modules
- optional_modules
- required_providers
- optional_providers
- access_tier
- output_template
- created_at
- updated_at
```

### Findings

```text
findings
- id
- case_id
- title
- severity
- confidence
- status
- summary
- evidence_refs
- source_modules
- created_at
- updated_at
```

### External Enrichment Events

```text
external_enrichment_events
- id
- case_id
- scan_id
- provider
- module_id
- target_kind
- target_hash
- status
- http_status
- rate_limit_remaining
- created_at
```

Do not store raw queried sensitive values in this event table unless necessary. Prefer hashes or references to case indicators.

---

## UI Plan

### Integrations Page

Replace flat cards with:

- access tier filters
- category filters
- configured/missing filters
- "free-only mode" toggle
- provider cards with setup/test/history
- workflow impact list: "used by Domain Recon Bot"

### Workflow Launcher

Add `/workflows`:

- choose workflow
- enter target
- see required providers
- see optional paid providers
- see estimated request usage
- choose free-only or enhanced mode
- launch case scan

### Case Findings Tab

Add a new case tab:

- Findings

Views:

- severity grouped
- confidence grouped
- source module filter
- convert graph selection to finding
- include/exclude finding from reports

### Admin Provider Policy

Add settings:

- allow paid providers
- allow restricted providers
- require confirmation before external submission
- require private/unlisted URL scan where provider supports it
- redact sensitive values in AI prompts

---

## Guardrails

- Do not scrape providers in ways that violate terms.
- Do not bypass authentication, quotas, or payment requirements.
- Do not store or expose plaintext credentials.
- Do not send sensitive case targets to third-party providers without clear user intent.
- Do not include raw restricted data in default reports.
- Do not claim a provider is free for commercial use unless verified.
- Pricing and access rules change; verify provider terms before implementation and before recommending purchases.

---

## External Provider Notes Verified During Planning

These notes are for planning only. Re-check before implementation or purchase.

- Shodan API docs require an API key in request examples and use query credits for some search behavior: https://developer.shodan.io/api
- VirusTotal API v3 is the recommended API and points professional users to VT Enterprise offerings for more quota/context: https://docs.virustotal.com/reference/overview
- AbuseIPDB has a free Individual plan and paid Basic/Premium/Enterprise plans: https://www.abuseipdb.com/pricing
- urlscan.io supports API keys, quotas/rate limits, and public/unlisted/private visibility levels: https://urlscan.io/docs/api/
- HIBP email breach/paste/domain APIs require an API subscription key; Pwned Passwords range API is free without subscription: https://haveibeenpwned.com/API/v3
- Hunter has Free through Enterprise plan tiers and includes API access in the pricing matrix: https://hunter.io/pricing
- Tomba advertises credits, API access, and paid monthly or one-time purchases: https://tomba.io/pricing
- IPinfo offers a free Lite tier plus paid Core/Plus/Max/Enterprise tiers: https://ipinfo.io/pricing
- Censys legacy search notes free users should use the new Censys Platform: https://search.censys.io/api
- GreyNoise has a Free tier and paid Standard/Advanced/Elite tiers with different API/search capability: https://www.greynoise.io/plans
- URLhaus Community API is free under fair-use principles, requires an Auth-Key, and commercial/for-profit use may require a paid enhanced API: https://urlhaus.abuse.ch/api/
- OpenPhish has a free Community feed and Premium/Platinum feeds by contact: https://openphish.com/phishing_feeds.html
- PhishTank provides downloadable phishing databases and recommends registering an application key for automated downloads: https://phishtank.org/developer_info.php

---

## Recommended Next Implementation Order

1. Add structured integration catalog metadata.
2. Update the Integrations UI to group by access tier and category.
3. Fix HIBP and urlscan access assumptions.
4. Add provider health checks and external enrichment event logging.
5. Add URLhaus, PhishTank, OpenPhish, CT logs, and GreyNoise Community.
6. Add workflow templates and `/workflows` launcher.
7. Add findings model and Case Findings tab.
8. Add paid-provider warning and free-only scan mode.
9. Add Censys, SecurityTrails, WhoisXML API, and BuiltWith after the credential foundation is stable.
10. Revisit restricted providers only after auth, RBAC, audit logging, and data classification are implemented.

---

## Definition Of Done

- Integrations are grouped by access tier and category.
- Provider metadata includes credential requirements, sensitivity, target submission behavior, and source URL.
- Existing integration assumptions are corrected.
- Free/community feed integrations improve coverage without paid dependencies.
- Workflows can explain which providers are required, optional, free, or paid.
- Paid/commercial providers require explicit configuration and operator opt-in.
- Restricted providers are blocked unless compliance controls exist.
- Reports and findings preserve provider/source citations.
