"""Graph Data API Endpoints"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.indicator import Indicator
from app.models.edge import Edge
from app.schemas.indicator import IndicatorResponse
from app.schemas.edge import EdgeResponse

router = APIRouter()


# Note: Edge.relationship field renamed to Edge.relationship_type to avoid SQLAlchemy conflict


@router.get("/nodes", response_model=List[IndicatorResponse])
async def get_nodes(
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """Get all graph nodes (indicators)"""
    result = await db.execute(
        select(Indicator)
        .order_by(Indicator.first_seen.desc())
        .offset(skip)
        .limit(limit)
    )
    nodes = result.scalars().all()
    return nodes


@router.get("/edges", response_model=List[EdgeResponse])
async def get_edges(
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """Get all graph edges (relationships)"""
    result = await db.execute(
        select(Edge)
        .order_by(Edge.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    edges = result.scalars().all()
    return edges


@router.get("/nodes/{node_id}", response_model=IndicatorResponse)
async def get_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get node by ID"""
    result = await db.execute(select(Indicator).where(Indicator.id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found"
        )
    
    return node
