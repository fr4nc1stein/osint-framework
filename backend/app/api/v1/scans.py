"""Scan Management API Endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.scan import Scan
from app.schemas.scan import ScanCreate, ScanResponse

router = APIRouter()


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create and launch a new scan"""
    scan = Scan(
        **scan_data.model_dump(),
        total_modules=len(scan_data.modules),
        status="queued"
    )
    
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # TODO: Enqueue tasks to arq worker (Phase 2)
    # for module_id in scan_data.modules:
    #     await enqueue_scan_task(scan.id, module_id, scan_data.seed_value, scan_data.seed_kind)
    
    return scan


@router.get("", response_model=List[ScanResponse])
async def list_scans(
    case_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List scans, optionally filtered by case"""
    query = select(Scan).order_by(Scan.created_at.desc())
    
    if case_id:
        query = query.where(Scan.case_id == case_id)
    
    result = await db.execute(query.offset(skip).limit(limit))
    scans = result.scalars().all()
    return scans


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get scan by ID"""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    return scan


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete/cancel scan"""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    # TODO: Cancel running tasks (Phase 2)
    
    await db.delete(scan)
    await db.commit()
