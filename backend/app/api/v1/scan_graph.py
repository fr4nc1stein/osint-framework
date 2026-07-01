"""Scan Graph API - Get graph data for a specific scan"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.scan import Scan
from app.services.graph_service import GraphService

router = APIRouter()


@router.get("/{scan_id}/graph")
async def get_scan_graph(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get graph data (nodes and edges) for a specific scan"""
    
    # Verify scan exists
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    # Get graph data
    graph_service = GraphService(db)
    graph_data = await graph_service.get_scan_graph(scan_id)
    
    return {
        "scan_id": str(scan_id),
        "status": scan.status,
        "progress": scan.progress,
        "total_modules": scan.total_modules,
        "module_statuses": scan.module_statuses,
        "graph": graph_data
    }
