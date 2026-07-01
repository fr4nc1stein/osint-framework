"""Scan Children API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.scan import Scan

router = APIRouter()


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
