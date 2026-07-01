"""Auto-Linker Service - Cross-correlation and relationship inference"""
from typing import List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
import uuid

from app.models.indicator import Indicator
from app.models.edge import Edge
from app.services.graph_service import GraphService


class AutoLinkerService:
    """
    Automatically creates cross-correlation edges between indicators
    discovered by different modules
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph_service = GraphService(db)
    
    async def find_corroborations(self, scan_id: uuid.UUID) -> List[Edge]:
        """
        Find indicators discovered by multiple modules in the same scan
        and create CORROBORATED_BY edges
        """
        
        # Get all edges for this scan
        from app.models.edge import scan_findings
        
        result = await self.db.execute(
            select(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(scan_findings.c.scan_id == scan_id)
        )
        edges = result.scalars().all()
        
        # Group edges by (src_id, dst_id, relationship_type)
        edge_groups: Dict[Tuple, List[Edge]] = {}
        
        for edge in edges:
            key = (edge.src_id, edge.dst_id, edge.relationship_type)
            if key not in edge_groups:
                edge_groups[key] = []
            edge_groups[key].append(edge)
        
        # Find groups with multiple modules (corroboration)
        corroboration_edges = []
        
        for key, group_edges in edge_groups.items():
            if len(group_edges) < 2:
                continue
            
            # Multiple modules found the same relationship
            modules = [e.source_module for e in group_edges]
            unique_modules = list(set(modules))
            
            if len(unique_modules) < 2:
                continue  # Same module multiple times, not corroboration
            
            # Calculate corroboration confidence
            # More modules = higher confidence
            base_confidence = sum(e.confidence for e in group_edges) / len(group_edges)
            module_bonus = min(0.1 * (len(unique_modules) - 1), 0.2)
            corroboration_confidence = min(base_confidence + module_bonus, 0.99)
            
            # Create CORROBORATED_BY edge between the first two edges
            for i in range(len(group_edges) - 1):
                for j in range(i + 1, len(group_edges)):
                    edge1 = group_edges[i]
                    edge2 = group_edges[j]
                    
                    # Create bidirectional corroboration edges
                    corr_edge = await self.graph_service.create_edge(
                        src_id=edge1.id,
                        dst_id=edge2.id,
                        relationship_type="CORROBORATED_BY",
                        confidence=corroboration_confidence,
                        source_module="auto_linker",
                        evidence={
                            "modules": unique_modules,
                            "discovery_count": len(group_edges),
                            "relationship": edge1.relationship_type
                        }
                    )
                    corroboration_edges.append(corr_edge)
        
        await self.db.commit()
        return corroboration_edges
    
    async def infer_relationships(self, scan_id: uuid.UUID) -> List[Edge]:
        """
        Infer new relationships based on existing graph patterns
        
        Examples:
        - If A RESOLVES_TO B and B BELONGS_TO C, infer A HOSTED_BY C
        - If A HAS_MX B and B RESOLVES_TO C, infer A EMAIL_HOSTED_BY C
        """
        
        inferred_edges = []
        
        # Pattern 1: Domain → IP → Organization
        # If domain resolves to IP, and IP belongs to org, domain is hosted by org
        pattern1_edges = await self._infer_hosting_relationship(scan_id)
        inferred_edges.extend(pattern1_edges)
        
        # Pattern 2: Email domain extraction
        # If email has domain, create reverse link
        pattern2_edges = await self._infer_email_domain_relationship(scan_id)
        inferred_edges.extend(pattern2_edges)
        
        await self.db.commit()
        return inferred_edges
    
    async def _infer_hosting_relationship(self, scan_id: uuid.UUID) -> List[Edge]:
        """
        Infer: Domain HOSTED_BY Organization
        From: Domain RESOLVES_TO IP, IP BELONGS_TO Organization
        """
        
        from app.models.edge import scan_findings
        
        # Find domain → IP edges
        result = await self.db.execute(
            select(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(
                and_(
                    scan_findings.c.scan_id == scan_id,
                    Edge.relationship_type == "RESOLVES_TO"
                )
            )
        )
        resolves_edges = result.scalars().all()
        
        inferred = []
        
        for resolves_edge in resolves_edges:
            # Get the IP indicator
            ip_id = resolves_edge.dst_id
            
            # Find IP → Organization edges
            result = await self.db.execute(
                select(Edge)
                .join(scan_findings, Edge.id == scan_findings.c.edge_id)
                .where(
                    and_(
                        scan_findings.c.scan_id == scan_id,
                        Edge.src_id == ip_id,
                        Edge.relationship_type == "BELONGS_TO"
                    )
                )
            )
            belongs_edges = result.scalars().all()
            
            for belongs_edge in belongs_edges:
                # Create inferred edge: Domain HOSTED_BY Organization
                inferred_edge = await self.graph_service.create_edge(
                    src_id=resolves_edge.src_id,  # Domain
                    dst_id=belongs_edge.dst_id,   # Organization
                    relationship_type="HOSTED_BY",
                    confidence=min(resolves_edge.confidence * belongs_edge.confidence, 0.85),
                    source_module="auto_linker",
                    evidence={
                        "inferred_from": [
                            str(resolves_edge.id),
                            str(belongs_edge.id)
                        ],
                        "inference_type": "transitive_hosting"
                    }
                )
                inferred.append(inferred_edge)
        
        return inferred
    
    async def _infer_email_domain_relationship(self, scan_id: uuid.UUID) -> List[Edge]:
        """
        Infer: Domain HAS_EMAIL Email
        From: Email EXTRACTED_FROM Domain
        """
        
        from app.models.edge import scan_findings
        
        # Find email → domain edges
        result = await self.db.execute(
            select(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(
                and_(
                    scan_findings.c.scan_id == scan_id,
                    Edge.relationship_type == "EXTRACTED_FROM"
                )
            )
        )
        extracted_edges = result.scalars().all()
        
        inferred = []
        
        for extracted_edge in extracted_edges:
            # Create reverse edge: Domain HAS_EMAIL Email
            inferred_edge = await self.graph_service.create_edge(
                src_id=extracted_edge.dst_id,  # Domain
                dst_id=extracted_edge.src_id,  # Email
                relationship_type="HAS_EMAIL",
                confidence=extracted_edge.confidence,
                source_module="auto_linker",
                evidence={
                    "inferred_from": [str(extracted_edge.id)],
                    "inference_type": "reverse_relationship"
                }
            )
            inferred.append(inferred_edge)
        
        return inferred
    
    async def get_correlation_stats(self, scan_id: uuid.UUID) -> Dict:
        """Get statistics about correlations in a scan"""
        
        from app.models.edge import scan_findings
        
        # Count total edges
        result = await self.db.execute(
            select(func.count(Edge.id))
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(scan_findings.c.scan_id == scan_id)
        )
        total_edges = result.scalar()
        
        # Count corroborated edges
        result = await self.db.execute(
            select(func.count(Edge.id))
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(
                and_(
                    scan_findings.c.scan_id == scan_id,
                    Edge.relationship_type == "CORROBORATED_BY"
                )
            )
        )
        corroborated_count = result.scalar()
        
        # Count inferred edges
        result = await self.db.execute(
            select(func.count(Edge.id))
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(
                and_(
                    scan_findings.c.scan_id == scan_id,
                    Edge.source_module == "auto_linker"
                )
            )
        )
        inferred_count = result.scalar()
        
        return {
            "total_edges": total_edges,
            "corroborated_edges": corroborated_count,
            "inferred_edges": inferred_count,
            "correlation_ratio": corroborated_count / total_edges if total_edges > 0 else 0
        }
