"""Scan Children & Module Suggestions API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.scan import Scan
from app.modules.registry import PLUGIN_REGISTRY, discover_modules

router = APIRouter()

# Node type → applicable module ids
NODE_MODULE_MAP = {
    "ip":       ["ip_geolocation", "abuseipdb", "shodan_lookup"],
    "domain":   ["dns_records", "whois_lookup", "subdomain_enum", "virustotal_domain", "urlscan_lookup"],
    "email":    ["hibp_breach", "email_domain"],
    "username": ["hibp_breach"],
    "phone":    [],
    "bitcoin":  [],
}


@router.get("/{scan_id}/children")
async def get_scan_children(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Return all child scans of a given scan"""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    result = await db.execute(
        select(Scan).where(Scan.parent_scan_id == scan_id).order_by(Scan.created_at)
    )
    children = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "parent_scan_id": str(s.parent_scan_id),
            "seed_value": s.seed_value,
            "seed_kind": s.seed_kind,
            "modules": s.modules,
            "status": s.status,
            "progress": s.progress,
            "total_modules": s.total_modules,
            "created_at": s.created_at.isoformat(),
        }
        for s in children
    ]


modules_router = APIRouter()


@modules_router.get("/suggest")
async def suggest_modules(node_type: str = "domain"):
    """Return applicable module ids for a given node type"""
    if not PLUGIN_REGISTRY:
        discover_modules()

    suggested_ids = NODE_MODULE_MAP.get(node_type.lower(), [])
    result = []
    for mod_id in suggested_ids:
        cls = PLUGIN_REGISTRY.get(mod_id)
        if cls:
            result.append({
                "module_id": cls.MODULE_ID,
                "name": cls.DISPLAY_NAME,
                "description": cls.DESCRIPTION,
                "requires_api_key": cls.REQUIRES_API_KEY,
            })
    return result
