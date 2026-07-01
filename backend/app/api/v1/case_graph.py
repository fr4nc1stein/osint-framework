"""Case Graph API — merges all scan graphs in a case"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.case import Case
from app.models.scan import Scan
from app.models.indicator import Indicator
from app.models.edge import Edge, scan_findings

router = APIRouter()


@router.get("/{case_id}/graph")
async def get_case_graph(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Return a merged graph of all scans in a case, with per-scan origin tags"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Load all scans for this case
    result = await db.execute(
        select(Scan).where(Scan.case_id == case_id).order_by(Scan.created_at)
    )
    scans = result.scalars().all()

    if not scans:
        return {"nodes": [], "edges": [], "scans": []}

    scan_ids = [s.id for s in scans]
    scan_index = {s.id: {"id": str(s.id), "seed_value": s.seed_value, "seed_kind": s.seed_kind} for s in scans}

    # Fetch all edges across all scans
    result = await db.execute(
        select(Edge, scan_findings.c.scan_id)
        .join(scan_findings, Edge.id == scan_findings.c.edge_id)
        .where(scan_findings.c.scan_id.in_(scan_ids))
    )
    rows = result.all()

    # Build edge map and collect indicator ids, tracking which scans each edge appears in
    edge_map: dict[uuid.UUID, dict] = {}
    indicator_scan_map: dict[uuid.UUID, set] = {}

    for edge, scan_id in rows:
        if edge.id not in edge_map:
            edge_map[edge.id] = {
                "id": str(edge.id),
                "source": str(edge.src_id),
                "target": str(edge.dst_id),
                "relationship": edge.relationship_type,
                "confidence": float(edge.confidence),
                "source_module": edge.source_module,
                "evidence": edge.evidence,
                "scan_origins": [],
            }
        scan_label = scan_index[scan_id]["seed_value"]
        if scan_label not in edge_map[edge.id]["scan_origins"]:
            edge_map[edge.id]["scan_origins"].append(scan_label)

        for ind_id in (edge.src_id, edge.dst_id):
            indicator_scan_map.setdefault(ind_id, set()).add(scan_id)

    # Fetch all unique indicators
    if indicator_scan_map:
        result = await db.execute(
            select(Indicator).where(Indicator.id.in_(list(indicator_scan_map.keys())))
        )
        indicators = result.scalars().all()
    else:
        indicators = []

    nodes = [
        {
            "id": str(ind.id),
            "kind": ind.kind,
            "value": ind.value,
            "label": ind.label,
            "meta": ind.meta,
            "confidence": float(ind.confidence) if ind.confidence else None,
            "scan_origins": [scan_index[sid]["seed_value"] for sid in indicator_scan_map.get(ind.id, [])],
        }
        for ind in indicators
    ]

    return {
        "nodes": nodes,
        "edges": list(edge_map.values()),
        "scans": [
            {"id": str(s.id), "seed_value": s.seed_value, "seed_kind": s.seed_kind, "status": s.status}
            for s in scans
        ],
    }


@router.get("/{case_id}/scans")
async def list_case_scans(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all scans in a case, including hierarchy (parent/child)"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    result = await db.execute(
        select(Scan)
        .where(Scan.case_id == case_id)
        .order_by(Scan.created_at)
    )
    scans = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "parent_scan_id": str(s.parent_scan_id) if s.parent_scan_id else None,
            "seed_value": s.seed_value,
            "seed_kind": s.seed_kind,
            "modules": s.modules,
            "status": s.status,
            "progress": s.progress,
            "total_modules": s.total_modules,
            "module_statuses": s.module_statuses,
            "created_at": s.created_at.isoformat(),
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
        }
        for s in scans
    ]
