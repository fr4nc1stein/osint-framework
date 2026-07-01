"""Graph Service - Auto-create indicators and edges from discoveries"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
import uuid

from app.models.indicator import Indicator
from app.models.edge import Edge
from app.schemas.module import DiscoveryResult


class GraphService:
    """Service for managing graph data (indicators and edges)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_indicator(
        self,
        kind: str,
        value: str,
        label: Optional[str] = None,
        meta: Optional[dict] = None,
        confidence: Optional[float] = None
    ) -> Indicator:
        """Get existing indicator or create new one"""
        
        # Normalize value (lowercase, strip whitespace)
        normalized_value = value.lower().strip()
        
        # Try to find existing indicator
        result = await self.db.execute(
            select(Indicator).where(
                Indicator.kind == kind,
                Indicator.value == normalized_value
            )
        )
        indicator = result.scalar_one_or_none()
        
        if indicator:
            # Update last_verified timestamp
            from datetime import datetime
            indicator.last_verified = datetime.utcnow()
            return indicator
        
        # Create new indicator
        indicator = Indicator(
            kind=kind,
            value=normalized_value,
            label=label or value,
            meta=meta or {},
            confidence=confidence
        )
        self.db.add(indicator)
        await self.db.flush()  # Get the ID without committing
        
        return indicator
    
    async def create_edge(
        self,
        src_id: uuid.UUID,
        dst_id: uuid.UUID,
        relationship_type: str,
        confidence: float,
        source_module: str,
        evidence: dict
    ) -> Edge:
        """Create edge between indicators (upsert)"""
        
        # Use PostgreSQL INSERT ... ON CONFLICT DO NOTHING
        stmt = insert(Edge).values(
            src_id=src_id,
            dst_id=dst_id,
            relationship_type=relationship_type,
            confidence=confidence,
            source_module=source_module,
            evidence=evidence
        ).on_conflict_do_nothing(
            index_elements=['src_id', 'dst_id', 'relationship_type', 'source_module']
        ).returning(Edge.id)
        
        result = await self.db.execute(stmt)
        edge_id = result.scalar_one_or_none()
        
        if edge_id:
            # New edge created
            result = await self.db.execute(
                select(Edge).where(Edge.id == edge_id)
            )
            return result.scalar_one()
        else:
            # Edge already exists, fetch it
            result = await self.db.execute(
                select(Edge).where(
                    Edge.src_id == src_id,
                    Edge.dst_id == dst_id,
                    Edge.relationship_type == relationship_type,
                    Edge.source_module == source_module
                )
            )
            return result.scalar_one()
    
    async def add_discovery(
        self,
        scan_id: uuid.UUID,
        discovery: DiscoveryResult
    ) -> Edge:
        """
        Process a discovery result:
        1. Create/get source indicator
        2. Create/get destination indicator
        3. Create edge between them
        4. Link edge to scan
        """
        
        # Create or get source indicator
        src_indicator = await self.get_or_create_indicator(
            kind=discovery.src_kind,
            value=discovery.src_value
        )
        
        # Create or get destination indicator
        dst_indicator = await self.get_or_create_indicator(
            kind=discovery.dst_kind,
            value=discovery.dst_value
        )
        
        # Create edge
        edge = await self.create_edge(
            src_id=src_indicator.id,
            dst_id=dst_indicator.id,
            relationship_type=discovery.relationship,
            confidence=discovery.confidence,
            source_module=discovery.source_module,
            evidence=discovery.evidence
        )
        
        # Link edge to scan (via scan_findings association table)
        from app.models.edge import scan_findings
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        
        stmt = pg_insert(scan_findings).values(
            scan_id=scan_id,
            edge_id=edge.id
        ).on_conflict_do_nothing()
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        return edge
    
    async def get_scan_graph(self, scan_id: uuid.UUID) -> dict:
        """Get all indicators and edges for a scan"""
        from app.models.edge import scan_findings
        
        # Get all edges for this scan
        result = await self.db.execute(
            select(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(scan_findings.c.scan_id == scan_id)
        )
        edges = result.scalars().all()
        
        # Collect unique indicator IDs
        indicator_ids = set()
        for edge in edges:
            indicator_ids.add(edge.src_id)
            indicator_ids.add(edge.dst_id)
        
        # Get all indicators
        if indicator_ids:
            result = await self.db.execute(
                select(Indicator).where(Indicator.id.in_(indicator_ids))
            )
            indicators = result.scalars().all()
        else:
            indicators = []
        
        return {
            "nodes": [
                {
                    "id": str(ind.id),
                    "kind": ind.kind,
                    "value": ind.value,
                    "label": ind.label,
                    "meta": ind.meta,
                    "confidence": float(ind.confidence) if ind.confidence else None
                }
                for ind in indicators
            ],
            "edges": [
                {
                    "id": str(edge.id),
                    "source": str(edge.src_id),
                    "target": str(edge.dst_id),
                    "relationship": edge.relationship_type,
                    "confidence": float(edge.confidence),
                    "source_module": edge.source_module,
                    "evidence": edge.evidence
                }
                for edge in edges
            ]
        }
