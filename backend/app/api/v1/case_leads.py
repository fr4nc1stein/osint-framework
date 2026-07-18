"""Case lead review queue API endpoints."""
from collections import Counter
from datetime import datetime, timezone
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.case import Case
from app.models.case_entity import CaseEntity
from app.models.case_geolocation import CaseGeolocation
from app.models.case_lead_review import CaseLeadReview
from app.models.case_relationship import CaseRelationship
from app.models.case_timeline import CaseTimelineEvent
from app.models.edge import Edge, scan_findings
from app.models.indicator import Indicator
from app.models.scan import Scan
from app.schemas.case_lead_review import CaseLeadItem, CaseLeadQueueResponse, CaseLeadReviewAction, CaseLeadReviewResponse

router = APIRouter()

OPEN_STATUSES = {"lead", "needs_review", "follow_up"}
REVIEW_STATUS_BY_ACTION = {
    "confirm": "confirmed",
    "reject": "rejected",
    "follow_up": "follow_up",
    "stale": "stale",
    "promote": "confirmed",
    "merge": "confirmed",
}


async def _ensure_case(case_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(select(Case.id).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")


async def _review_map(case_id: uuid.UUID, db: AsyncSession) -> dict[tuple[str, uuid.UUID], CaseLeadReview]:
    result = await db.execute(select(CaseLeadReview).where(CaseLeadReview.case_id == case_id))
    return {(review.target_type, review.target_id): review for review in result.scalars().all()}


async def _get_or_create_review(
    case_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID,
    db: AsyncSession,
) -> CaseLeadReview:
    result = await db.execute(
        select(CaseLeadReview)
        .where(CaseLeadReview.case_id == case_id)
        .where(CaseLeadReview.target_type == target_type)
        .where(CaseLeadReview.target_id == target_id)
    )
    review = result.scalar_one_or_none()
    if review:
        return review
    review = CaseLeadReview(case_id=case_id, target_type=target_type, target_id=target_id)
    db.add(review)
    await db.flush()
    return review


def _include_status(review_status: str, status_filter: str) -> bool:
    if status_filter == "all":
        return True
    if status_filter == "open":
        return review_status in OPEN_STATUSES
    return review_status == status_filter


def _lead_item(
    *,
    target_type: str,
    target_id: uuid.UUID,
    lead_type: str,
    label: str,
    source_type: str,
    review_status: str,
    value: str | None = None,
    description: str | None = None,
    relationship: str | None = None,
    source_ref: str | None = None,
    source_module: str | None = None,
    confidence: float | None = None,
    created_at=None,
    updated_at=None,
    scan_origins: list[str] | None = None,
    review: CaseLeadReview | None = None,
    properties: dict | None = None,
) -> CaseLeadItem:
    return CaseLeadItem(
        id=f"{target_type}:{target_id}",
        target_type=target_type,
        target_id=target_id,
        lead_type=lead_type,
        label=label,
        value=value,
        description=description,
        relationship=relationship,
        source_type=source_type,
        source_ref=source_ref,
        source_module=source_module,
        review_status=review_status,
        confidence=confidence,
        created_at=created_at,
        updated_at=updated_at,
        scan_origins=scan_origins or [],
        promoted_entity_id=review.promoted_entity_id if review else None,
        merged_entity_id=review.merged_entity_id if review else None,
        notes=review.notes if review else None,
        properties=properties or {},
    )


async def _scan_context(case_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Scan).where(Scan.case_id == case_id).order_by(Scan.created_at))
    scans = result.scalars().all()
    scan_ids = [scan.id for scan in scans]
    scan_index = {scan.id: scan for scan in scans}
    if not scan_ids:
        return [], [], {}

    result = await db.execute(
        select(Edge, scan_findings.c.scan_id)
        .join(scan_findings, Edge.id == scan_findings.c.edge_id)
        .where(scan_findings.c.scan_id.in_(scan_ids))
    )
    edge_rows = result.all()
    indicator_ids = {edge.src_id for edge, _ in edge_rows} | {edge.dst_id for edge, _ in edge_rows}
    if indicator_ids:
        result = await db.execute(select(Indicator).where(Indicator.id.in_(list(indicator_ids))))
        indicators = result.scalars().all()
    else:
        indicators = []
    indicator_scan_map: dict[uuid.UUID, set[uuid.UUID]] = {}
    edge_scan_map: dict[uuid.UUID, set[uuid.UUID]] = {}
    for edge, scan_id in edge_rows:
        edge_scan_map.setdefault(edge.id, set()).add(scan_id)
        indicator_scan_map.setdefault(edge.src_id, set()).add(scan_id)
        indicator_scan_map.setdefault(edge.dst_id, set()).add(scan_id)
    context = {
        "scan_index": scan_index,
        "indicator_scan_map": indicator_scan_map,
        "edge_scan_map": edge_scan_map,
        "indicator_index": {indicator.id: indicator for indicator in indicators},
    }
    return indicators, [edge for edge, _ in edge_rows], context


@router.get("/{case_id}/leads", response_model=CaseLeadQueueResponse)
async def list_case_leads(
    case_id: uuid.UUID,
    status: str = Query(default="open", pattern="^(open|all|lead|needs_review|follow_up|confirmed|rejected|stale)$"),
    lead_type: str = Query(default="all"),
    db: AsyncSession = Depends(get_db),
):
    """Return the case lead queue across manual objects and scan-derived findings."""
    await _ensure_case(case_id, db)
    reviews = await _review_map(case_id, db)
    items: list[CaseLeadItem] = []

    result = await db.execute(select(CaseEntity).where(CaseEntity.case_id == case_id).order_by(CaseEntity.created_at.desc()))
    for entity in result.scalars().all():
        if not _include_status(entity.verification_status, status):
            continue
        items.append(_lead_item(
            target_type="entity",
            target_id=entity.id,
            lead_type=entity.type,
            label=entity.label or entity.value,
            value=entity.value,
            description=entity.description,
            source_type=entity.source_type,
            source_ref=entity.source_ref,
            review_status=entity.verification_status,
            confidence=float(entity.confidence) if entity.confidence is not None else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            properties=entity.properties or {},
        ))

    result = await db.execute(select(CaseRelationship).where(CaseRelationship.case_id == case_id).order_by(CaseRelationship.created_at.desc()))
    for rel in result.scalars().all():
        if not _include_status(rel.verification_status, status):
            continue
        items.append(_lead_item(
            target_type="relationship",
            target_id=rel.id,
            lead_type="relationship",
            label=rel.label or rel.relationship_type,
            description=rel.description,
            relationship=rel.relationship_type,
            source_type=rel.source_type,
            source_ref=rel.source_ref,
            review_status=rel.verification_status,
            confidence=float(rel.confidence) if rel.confidence is not None else None,
            created_at=rel.created_at,
            updated_at=rel.updated_at,
            properties=rel.properties or {},
        ))

    result = await db.execute(select(CaseTimelineEvent).where(CaseTimelineEvent.case_id == case_id).order_by(CaseTimelineEvent.created_at.desc()))
    for event in result.scalars().all():
        if not _include_status(event.verification_status, status):
            continue
        items.append(_lead_item(
            target_type="timeline_event",
            target_id=event.id,
            lead_type=event.event_type,
            label=event.title,
            description=event.description,
            source_type=event.source_type,
            source_ref=event.source_ref,
            review_status=event.verification_status,
            confidence=float(event.confidence) if event.confidence is not None else None,
            created_at=event.created_at,
            updated_at=event.updated_at,
        ))

    result = await db.execute(select(CaseGeolocation).where(CaseGeolocation.case_id == case_id).order_by(CaseGeolocation.created_at.desc()))
    for geo in result.scalars().all():
        if not _include_status(geo.verification_status, status):
            continue
        items.append(_lead_item(
            target_type="geolocation",
            target_id=geo.id,
            lead_type="geolocation",
            label=geo.label or geo.address_text or "Location observation",
            value=geo.address_text,
            description=geo.notes,
            source_type=geo.source_type,
            source_ref=geo.source_ref,
            review_status=geo.verification_status,
            confidence=float(geo.confidence) if geo.confidence is not None else None,
            created_at=geo.created_at,
            updated_at=geo.updated_at,
            properties={"latitude": float(geo.latitude), "longitude": float(geo.longitude), "precision": geo.precision},
        ))

    indicators, edges, context = await _scan_context(case_id, db)
    scan_index = context.get("scan_index", {})
    indicator_scan_map = context.get("indicator_scan_map", {})
    edge_scan_map = context.get("edge_scan_map", {})
    indicator_index = context.get("indicator_index", {})

    for indicator in indicators:
        review = reviews.get(("indicator", indicator.id))
        review_status = review.review_status if review else "needs_review"
        if not _include_status(review_status, status):
            continue
        scan_origins = [scan_index[sid].seed_value for sid in indicator_scan_map.get(indicator.id, set()) if sid in scan_index]
        items.append(_lead_item(
            target_type="indicator",
            target_id=indicator.id,
            lead_type=indicator.kind,
            label=indicator.label or indicator.value,
            value=indicator.value,
            source_type="scan",
            review_status=review_status,
            confidence=float(indicator.confidence) if indicator.confidence is not None else None,
            created_at=indicator.first_seen,
            updated_at=indicator.last_verified,
            scan_origins=scan_origins,
            review=review,
            properties=indicator.meta or {},
        ))

    seen_edges: set[uuid.UUID] = set()
    for edge in edges:
        if edge.id in seen_edges:
            continue
        seen_edges.add(edge.id)
        review = reviews.get(("graph_edge", edge.id))
        review_status = review.review_status if review else "needs_review"
        if not _include_status(review_status, status):
            continue
        src = indicator_index.get(edge.src_id)
        dst = indicator_index.get(edge.dst_id)
        scan_origins = [scan_index[sid].seed_value for sid in edge_scan_map.get(edge.id, set()) if sid in scan_index]
        items.append(_lead_item(
            target_type="graph_edge",
            target_id=edge.id,
            lead_type="relationship",
            label=edge.relationship_type,
            description=f"{src.value if src else edge.src_id} {edge.relationship_type.replace('_', ' ')} {dst.value if dst else edge.dst_id}",
            relationship=edge.relationship_type,
            source_type="scan",
            source_module=edge.source_module,
            review_status=review_status,
            confidence=float(edge.confidence) if edge.confidence is not None else None,
            created_at=edge.created_at,
            scan_origins=scan_origins,
            review=review,
            properties=edge.evidence or {},
        ))

    if lead_type != "all":
        items = [item for item in items if item.lead_type == lead_type or item.target_type == lead_type]

    items.sort(key=lambda item: (item.review_status in OPEN_STATUSES, item.created_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    by_status = Counter(item.review_status for item in items)
    by_target_type = Counter(item.target_type for item in items)
    return {
        "items": items,
        "counts": {
            "total": len(items),
            "open": len([item for item in items if item.review_status in OPEN_STATUSES]),
            "by_status": dict(by_status),
            "by_target_type": dict(by_target_type),
        },
    }


@router.patch("/{case_id}/leads/{target_type}/{target_id}", response_model=CaseLeadReviewResponse)
async def review_case_lead(
    case_id: uuid.UUID,
    target_type: Literal["entity", "relationship", "timeline_event", "geolocation", "indicator", "graph_edge"],
    target_id: uuid.UUID,
    body: CaseLeadReviewAction,
    db: AsyncSession = Depends(get_db),
):
    """Apply an analyst review action to a lead."""
    await _ensure_case(case_id, db)
    next_status = REVIEW_STATUS_BY_ACTION[body.action]
    reviewed_at = datetime.now(timezone.utc)
    promoted_entity_id = None

    if target_type == "entity":
        result = await db.execute(select(CaseEntity).where(CaseEntity.id == target_id, CaseEntity.case_id == case_id))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="Entity lead not found")
        target.verification_status = next_status
        if body.confidence is not None:
            target.confidence = body.confidence

    elif target_type == "relationship":
        result = await db.execute(select(CaseRelationship).where(CaseRelationship.id == target_id, CaseRelationship.case_id == case_id))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="Relationship lead not found")
        target.verification_status = next_status
        if body.confidence is not None:
            target.confidence = body.confidence

    elif target_type == "timeline_event":
        result = await db.execute(select(CaseTimelineEvent).where(CaseTimelineEvent.id == target_id, CaseTimelineEvent.case_id == case_id))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="Timeline lead not found")
        target.verification_status = next_status
        if body.confidence is not None:
            target.confidence = body.confidence

    elif target_type == "geolocation":
        result = await db.execute(select(CaseGeolocation).where(CaseGeolocation.id == target_id, CaseGeolocation.case_id == case_id))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="Geolocation lead not found")
        target.verification_status = next_status
        if body.confidence is not None:
            target.confidence = body.confidence

    elif target_type == "indicator":
        result = await db.execute(
            select(Indicator)
            .select_from(Indicator)
            .join(Edge, or_(Edge.src_id == Indicator.id, Edge.dst_id == Indicator.id))
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .join(Scan, Scan.id == scan_findings.c.scan_id)
            .where(Indicator.id == target_id, Scan.case_id == case_id)
            .limit(1)
        )
        indicator = result.scalar_one_or_none()
        if not indicator:
            raise HTTPException(status_code=404, detail="Scan indicator lead not found")
        if body.action == "promote":
            entity = CaseEntity(
                case_id=case_id,
                type=indicator.kind,
                label=indicator.label or indicator.value,
                value=indicator.value,
                properties={"promoted_from": "indicator", "indicator_id": str(indicator.id), **(indicator.meta or {})},
                source_type="scan",
                source_ref=str(indicator.id),
                confidence=body.confidence if body.confidence is not None else indicator.confidence,
                verification_status="confirmed",
            )
            db.add(entity)
            await db.flush()
            promoted_entity_id = entity.id
        elif body.action == "merge":
            if not body.merged_entity_id:
                raise HTTPException(status_code=422, detail="merged_entity_id is required for merge")
            result = await db.execute(select(CaseEntity.id).where(CaseEntity.id == body.merged_entity_id, CaseEntity.case_id == case_id))
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Merge target is not a manual entity in this case")

    elif target_type == "graph_edge":
        result = await db.execute(
            select(Edge.id)
            .select_from(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .join(Scan, Scan.id == scan_findings.c.scan_id)
            .where(Edge.id == target_id, Scan.case_id == case_id)
            .limit(1)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Scan relationship lead not found")

    review = await _get_or_create_review(case_id, target_type, target_id, db)
    review.review_status = next_status
    review.notes = body.notes
    review.reviewed_by = body.reviewed_by
    review.reviewed_at = reviewed_at
    review.promoted_entity_id = promoted_entity_id or review.promoted_entity_id
    review.merged_entity_id = body.merged_entity_id or review.merged_entity_id
    review.meta = {**(review.meta or {}), "last_action": body.action}

    await db.commit()
    await db.refresh(review)
    return review
