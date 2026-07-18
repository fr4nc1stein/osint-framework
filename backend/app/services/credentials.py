"""Credential provider — DB-first lookup with .env fallback and Redis cache."""
from __future__ import annotations

import json
import os
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.crypto import decrypt
from app.models.integration_credential import IntegrationCredential

# Map provider id → env var name (for .env fallback)
PROVIDER_ENV_MAP: dict[str, str] = {
    "shodan":     "SHODAN_API_KEY",
    "virustotal": "VIRUSTOTAL_API_KEY",
    "abuseipdb":  "ABUSEIPDB_API_KEY",
    "tomba":      "TOMBA_API_KEY",
    "hibp":       "HIBP_API_KEY",
    "hunter":     "HUNTER_API_KEY",
    "ipinfo":     "IPINFO_TOKEN",
    "alienvault": "ALIENVAULT_API_KEY",
    "censys":     "CENSYS_API_KEY",
    "urlscan":    "URLSCAN_API_KEY",
    "mapbox":     "MAPBOX_TOKEN",
}

PROVIDER_ENV_FALLBACKS: dict[str, list[str]] = {
    "mapbox": ["VITE_MAPBOX_TOKEN"],
}

_CACHE_TTL = int(os.getenv("CRED_CACHE_TTL", "60"))


async def _get_redis():
    from app.core.redis import get_redis
    return await get_redis()


def get_env_api_key(provider: str) -> Optional[str]:
    """Return provider key from preferred env var or approved compatibility aliases."""
    env_names = [PROVIDER_ENV_MAP.get(provider), *PROVIDER_ENV_FALLBACKS.get(provider, [])]
    for env_name in env_names:
        if not env_name:
            continue
        value = os.getenv(env_name)
        if value:
            return value
    return None


async def get_api_key(provider: str, db: AsyncSession) -> Optional[str]:
    """
    Return the plaintext API key for a provider.
    Order: Redis cache → DB (decrypted) → .env fallback → None.
    Never raises — returns None if unconfigured.
    """
    cache_key = f"cred:{provider}:api_key"

    # 1. Redis cache
    try:
        redis = await _get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return cached.decode()
    except Exception:
        pass

    # 2. DB
    try:
        result = await db.execute(
            select(IntegrationCredential)
            .where(IntegrationCredential.provider == provider)
            .where(IntegrationCredential.enabled == True)
        )
        cred = result.scalar_one_or_none()
        if cred and cred.encrypted_key:
            plaintext = decrypt(cred.encrypted_key)
            # Cache it
            try:
                redis = await _get_redis()
                await redis.setex(cache_key, _CACHE_TTL, plaintext)
            except Exception:
                pass
            return plaintext
    except Exception:
        pass

    # 3. .env fallback
    value = get_env_api_key(provider)
    if value:
        return value

    return None


async def invalidate_cache(provider: str) -> None:
    """Clear Redis cache for a provider after credential update."""
    try:
        redis = await _get_redis()
        await redis.delete(f"cred:{provider}:api_key")
    except Exception:
        pass


async def get_source(provider: str, db: AsyncSession) -> str:
    """Return 'db', 'env_fallback', or 'unconfigured'."""
    try:
        result = await db.execute(
            select(IntegrationCredential)
            .where(IntegrationCredential.provider == provider)
            .where(IntegrationCredential.enabled == True)
        )
        cred = result.scalar_one_or_none()
        if cred and cred.encrypted_key:
            return "db"
    except Exception:
        pass

    if get_env_api_key(provider):
        return "env_fallback"

    return "unconfigured"
