"""Scan Management API Endpoints"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
import uuid

from app.core.database import get_db
from app.core.queue import get_queue
from app.models.case import Case
from app.models.case_entity import CaseEntity
from app.models.edge import Edge, scan_findings
from app.models.indicator import Indicator
from app.models.scan import Scan
from app.modules.registry import get_module
from app.schemas.scan import ScanCreate, ScanResponse

router = APIRouter()


async def _ensure_case(case_id: uuid.UUID | None, db: AsyncSession) -> None:
    if not case_id:
        return
    result = await db.execute(select(Case.id).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")


async def _validate_parent_scan(scan_data: ScanCreate, db: AsyncSession) -> None:
    if not scan_data.parent_scan_id:
        return
    result = await db.execute(select(Scan).where(Scan.id == scan_data.parent_scan_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=400, detail="Parent scan is not valid")
    if scan_data.case_id and parent.case_id and parent.case_id != scan_data.case_id:
        raise HTTPException(status_code=400, detail="Parent scan belongs to a different case")


async def _validate_source_node(scan_data: ScanCreate, db: AsyncSession) -> None:
    if not scan_data.source_node_type and not scan_data.source_node_id:
        return
    if not scan_data.case_id:
        raise HTTPException(status_code=422, detail="case_id is required when source_node_id is provided")
    if not scan_data.source_node_type or not scan_data.source_node_id:
        raise HTTPException(status_code=422, detail="source_node_type and source_node_id must be provided together")

    if scan_data.source_node_type == "entity":
        result = await db.execute(
            select(CaseEntity.id).where(
                CaseEntity.id == scan_data.source_node_id,
                CaseEntity.case_id == scan_data.case_id,
            )
        )
        exists = result.scalar_one_or_none()
    elif scan_data.source_node_type == "indicator":
        result = await db.execute(
            select(Indicator.id)
            .select_from(Indicator)
            .join(Edge, or_(Edge.src_id == Indicator.id, Edge.dst_id == Indicator.id))
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .join(Scan, Scan.id == scan_findings.c.scan_id)
            .where(Indicator.id == scan_data.source_node_id, Scan.case_id == scan_data.case_id)
            .limit(1)
        )
        exists = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(Edge.id)
            .select_from(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .join(Scan, Scan.id == scan_findings.c.scan_id)
            .where(Edge.id == scan_data.source_node_id, Scan.case_id == scan_data.case_id)
            .limit(1)
        )
        exists = result.scalar_one_or_none()

    if not exists:
        raise HTTPException(status_code=400, detail="Source node is not part of this case")


def _validate_modules(scan_data: ScanCreate) -> None:
    accepted_kind = scan_data.seed_kind.lower()
    seen_modules: set[str] = set()
    for module_id in scan_data.modules:
        if module_id in seen_modules:
            raise HTTPException(status_code=400, detail=f"Duplicate module selected: {module_id}")
        seen_modules.add(module_id)
        module = get_module(module_id)
        if not module:
            raise HTTPException(status_code=400, detail=f"Unknown module: {module_id}")
        accepted = {kind.lower() for kind in module.accepts}
        if accepted_kind not in accepted:
            raise HTTPException(
                status_code=400,
                detail=f"Module {module_id} does not support {scan_data.seed_kind} targets",
            )


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create and launch a new scan"""
    await _ensure_case(scan_data.case_id, db)
    await _validate_parent_scan(scan_data, db)
    await _validate_source_node(scan_data, db)
    _validate_modules(scan_data)

    scan = Scan(
        **scan_data.model_dump(),
        total_modules=len(scan_data.modules),
        module_statuses={
            module_id: {"status": "queued"}
            for module_id in scan_data.modules
        },
        status="queued"
    )
    
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # Enqueue tasks to arq worker
    queue = await get_queue()
    
    for module_id in scan_data.modules:
        await queue.enqueue_job(
            'run_scan_task',
            str(scan.id),
            module_id,
            scan_data.seed_value,
            scan_data.seed_kind
        )
    
    # Update scan status to running
    scan.status = "running"
    scan.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(scan)
    
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
