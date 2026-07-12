"""Integrations API — DB-backed credential management with .env fallback."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.crypto import encrypt, mask_hint, decrypt
from app.models.integration_credential import IntegrationCredential
from app.schemas.integration import IntegrationSave, IntegrationResponse
from app.services.credentials import PROVIDER_ENV_MAP, get_api_key, invalidate_cache

router = APIRouter()

# ── Catalog ──────────────────────────────────────────────────────────────────

CATALOG = [
    {"id": "shodan",      "name": "Shodan",            "description": "Port scanning & banner grabbing",       "category": "recon"},
    {"id": "virustotal",  "name": "VirusTotal",        "description": "File & URL reputation scoring",         "category": "threat"},
    {"id": "abuseipdb",   "name": "AbuseIPDB",         "description": "IP reputation & abuse reports",         "category": "threat"},
    {"id": "tomba",       "name": "Tomba.io",          "description": "Email discovery & verification",        "category": "email"},
    {"id": "hibp",        "name": "Have I Been Pwned", "description": "Data breach checking",                  "category": "breach"},
    {"id": "hunter",      "name": "Hunter.io",         "description": "Email finder & verification",           "category": "email"},
    {"id": "ipinfo",      "name": "IPinfo",            "description": "IP geolocation & ASN data",             "category": "recon"},
    {"id": "alienvault",  "name": "AlienVault OTX",   "description": "Open threat intelligence platform",     "category": "threat"},
    {"id": "censys",      "name": "Censys",            "description": "Internet-wide scanning & certificates", "category": "recon"},
    {"id": "urlscan",     "name": "URLScan.io",        "description": "URL & domain sandbox scanning",        "category": "threat"},
]

CATALOG_MAP = {c["id"]: c for c in CATALOG}


# ── Test functions per provider ───────────────────────────────────────────────

async def _test_provider(provider: str, api_key: str) -> tuple[str, str]:
    """Return (status, message) — 'ok' or 'fail'."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if provider == "shodan":
                r = await client.get(f"https://api.shodan.io/api-info?key={api_key}")
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "virustotal":
                r = await client.get("https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8",
                                     headers={"x-apikey": api_key})
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "abuseipdb":
                r = await client.get("https://api.abuseipdb.com/api/v2/check",
                                     params={"ipAddress": "8.8.8.8", "maxAgeInDays": 90},
                                     headers={"Key": api_key, "Accept": "application/json"})
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "urlscan":
                r = await client.get("https://urlscan.io/api/v1/user/quotas/",
                                     headers={"API-Key": api_key})
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "hibp":
                r = await client.get("https://haveibeenpwned.com/api/v3/breaches",
                                     headers={"hibp-api-key": api_key, "User-Agent": "OSIF-v2"})
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "hunter":
                r = await client.get(f"https://api.hunter.io/v2/account?api_key={api_key}")
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "ipinfo":
                r = await client.get(f"https://ipinfo.io/8.8.8.8?token={api_key}")
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "alienvault":
                r = await client.get("https://otx.alienvault.com/api/v1/user/me",
                                     headers={"X-OTX-API-KEY": api_key})
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "tomba":
                secret = os.getenv("TOMBA_SECRET_KEY", "")
                r = await client.get("https://api.tomba.io/v1/me",
                                     headers={"X-Tomba-Key": api_key, "X-Tomba-Secret": secret})
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            elif provider == "censys":
                # censys key is "id:secret" format
                parts = api_key.split(":", 1)
                auth = (parts[0], parts[1]) if len(parts) == 2 else (api_key, "")
                r = await client.get("https://search.censys.io/api/v1/account", auth=auth)
                if r.status_code == 200:
                    return "ok", "Connected successfully"
                return "fail", f"HTTP {r.status_code}"

            return "fail", f"No test defined for {provider}"
    except Exception as e:
        return "fail", str(e)[:120]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create(provider: str, db: AsyncSession) -> IntegrationCredential:
    result = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.provider == provider)
    )
    cred = result.scalar_one_or_none()
    if not cred:
        meta = CATALOG_MAP.get(provider, {})
        cred = IntegrationCredential(
            provider=provider,
            display_name=meta.get("name", provider),
        )
        db.add(cred)
        await db.flush()
    return cred


def _build_response(cred: Optional[IntegrationCredential], meta: dict, env_var: str) -> dict:
    """Merge DB row + catalog meta into a safe response dict."""
    env_configured = bool(os.getenv(env_var))

    if cred and cred.encrypted_key:
        has_key = True
        masked  = cred.masked_hint or "...?????"
        source  = "db"
        enabled = cred.enabled
        last_tested_at     = cred.last_tested_at
        last_test_status   = cred.last_test_status
        last_test_message  = cred.last_test_message
    elif env_configured:
        has_key = True
        masked  = None
        source  = "env_fallback"
        enabled = True
        last_tested_at = last_test_status = last_test_message = None
    else:
        has_key = False
        masked  = None
        source  = "unconfigured"
        enabled = cred.enabled if cred else True
        last_tested_at = last_test_status = last_test_message = None

    return {
        "id":               meta["id"],
        "provider":         meta["id"],
        "display_name":     meta["name"],
        "description":      meta["description"],
        "category":         meta["category"],
        "enabled":          enabled,
        "has_key":          has_key,
        "masked_hint":      masked,
        "source":           source,
        "last_tested_at":   last_tested_at,
        "last_test_status": last_test_status,
        "last_test_message":last_test_message,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def list_integrations(db: AsyncSession = Depends(get_db)):
    """Return full catalog with live configured/health status."""
    result = await db.execute(select(IntegrationCredential))
    cred_map = {c.provider: c for c in result.scalars().all()}

    return [
        _build_response(cred_map.get(item["id"]), item, PROVIDER_ENV_MAP.get(item["id"], ""))
        for item in CATALOG
    ]


@router.get("/{provider}")
async def get_integration(provider: str, db: AsyncSession = Depends(get_db)):
    if provider not in CATALOG_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    result = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.provider == provider)
    )
    cred = result.scalar_one_or_none()
    meta = CATALOG_MAP[provider]
    return _build_response(cred, meta, PROVIDER_ENV_MAP.get(provider, ""))


@router.put("/{provider}")
async def save_integration(
    provider: str,
    body: IntegrationSave,
    db: AsyncSession = Depends(get_db),
):
    """Save or update encrypted credential for a provider."""
    if provider not in CATALOG_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    if not body.api_key.strip():
        raise HTTPException(status_code=422, detail="api_key must not be empty")

    cred = await _get_or_create(provider, db)
    cred.encrypted_key  = encrypt(body.api_key.strip())
    cred.masked_hint    = mask_hint(body.api_key.strip())
    cred.enabled        = body.enabled
    cred.source         = "db"

    await db.commit()
    await db.refresh(cred)
    await invalidate_cache(provider)

    return _build_response(cred, CATALOG_MAP[provider], PROVIDER_ENV_MAP.get(provider, ""))


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(provider: str, db: AsyncSession = Depends(get_db)):
    """Remove stored DB credential (falls back to .env if set)."""
    if provider not in CATALOG_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    result = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.provider == provider)
    )
    cred = result.scalar_one_or_none()
    if cred:
        cred.encrypted_key = None
        cred.masked_hint   = None
        cred.source        = "unconfigured"
        await db.commit()
        await invalidate_cache(provider)


@router.post("/{provider}/test")
async def test_integration(provider: str, db: AsyncSession = Depends(get_db)):
    """Verify credentials by making a real API call."""
    if provider not in CATALOG_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    api_key = await get_api_key(provider, db)
    if not api_key:
        raise HTTPException(status_code=422, detail="No API key configured for this provider")

    test_status, test_message = await _test_provider(provider, api_key)

    # Persist test result
    cred = await _get_or_create(provider, db)
    cred.last_tested_at    = datetime.utcnow()
    cred.last_test_status  = test_status
    cred.last_test_message = test_message
    await db.commit()

    return {"status": test_status, "message": test_message}


@router.post("/import-env")
async def import_from_env(db: AsyncSession = Depends(get_db)):
    """One-time import of .env API keys into the DB."""
    imported = []
    for provider, env_var in PROVIDER_ENV_MAP.items():
        value = os.getenv(env_var)
        if not value:
            continue
        cred = await _get_or_create(provider, db)
        if cred.encrypted_key:
            continue  # already in DB — don't overwrite
        cred.encrypted_key = encrypt(value)
        cred.masked_hint   = mask_hint(value)
        cred.source        = "db"
        imported.append(provider)

    if imported:
        await db.commit()
        for p in imported:
            await invalidate_cache(p)

    return {"imported": imported, "count": len(imported)}
