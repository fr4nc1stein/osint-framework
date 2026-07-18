"""Geocoding provider abstraction for case map workflows."""
from __future__ import annotations

import httpx
from urllib.parse import quote
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.credentials import get_api_key


def _precision_from_mapbox(feature: dict) -> str:
    types = set(feature.get("place_type") or [])
    if "address" in types:
        return "building"
    if "poi" in types:
        return "exact"
    if "place" in types or "locality" in types or "neighborhood" in types:
        return "city"
    if "region" in types or "district" in types:
        return "region"
    if "country" in types:
        return "country"
    return "unknown"


async def geocode_address(provider: str, query: str, limit: int, db: AsyncSession) -> list[dict]:
    """Return normalized geocode candidates from the configured provider."""
    if provider != "mapbox":
        raise ValueError(f"Unsupported geocoding provider: {provider}")

    token = await get_api_key("mapbox", db)
    if not token:
        return []

    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(query, safe='')}.json",
            params={
                "access_token": token,
                "limit": limit,
                "types": "address,poi,place,locality,neighborhood,region,country",
            },
        )
        response.raise_for_status()
        payload = response.json()

    results = []
    for feature in payload.get("features", []):
        center = feature.get("center") or []
        if len(center) != 2:
            continue
        longitude, latitude = center
        relevance = feature.get("relevance")
        results.append({
            "provider": "mapbox",
            "label": feature.get("text") or feature.get("place_name") or query,
            "address_text": feature.get("place_name") or query,
            "latitude": latitude,
            "longitude": longitude,
            "precision": _precision_from_mapbox(feature),
            "confidence": relevance if isinstance(relevance, (int, float)) else None,
            "source_ref": feature.get("id"),
        })
    return results
