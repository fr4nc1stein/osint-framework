"""Case dossier API for analyst briefing views."""
from collections import Counter
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.case import Case
from app.models.case_entity import CaseEntity
from app.models.case_geolocation import CaseGeolocation
from app.models.case_lead_review import CaseLeadReview
from app.models.case_relationship import CaseRelationship
from app.models.case_timeline import CaseTimelineEvent
from app.models.edge import Edge, scan_findings
from app.models.evidence import Evidence
from app.models.indicator import Indicator
from app.models.scan import Scan

router = APIRouter()

CONFIRMED_STATUSES = {"confirmed"}
OPEN_LEAD_STATUSES = {"lead", "needs_review", "follow_up"}
SENSITIVE_EVIDENCE_TYPES = {"legal_document", "identity_document", "private_message", "financial_record"}


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _confidence(value) -> float | None:
    return float(value) if value is not None else None


def _entity_item(entity: CaseEntity) -> dict:
    return {
        "id": str(entity.id),
        "type": entity.type,
        "label": entity.label,
        "value": entity.value,
        "description": entity.description,
        "confidence": _confidence(entity.confidence),
        "verification_status": entity.verification_status,
        "source_type": entity.source_type,
        "source_ref": entity.source_ref,
        "properties": entity.properties or {},
        "created_at": _iso(entity.created_at),
        "updated_at": _iso(entity.updated_at),
    }


def _relationship_item(relationship: CaseRelationship, entity_index: dict[uuid.UUID, CaseEntity]) -> dict:
    source = entity_index.get(relationship.from_node_id)
    target = entity_index.get(relationship.to_node_id)
    return {
        "id": str(relationship.id),
        "relationship": relationship.relationship_type,
        "label": relationship.label or relationship.relationship_type.replace("_", " "),
        "description": relationship.description,
        "source": {
            "node_type": relationship.from_node_type,
            "id": str(relationship.from_node_id),
            "label": source.label if source else None,
            "value": source.value if source else None,
            "type": source.type if source else None,
        },
        "target": {
            "node_type": relationship.to_node_type,
            "id": str(relationship.to_node_id),
            "label": target.label if target else None,
            "value": target.value if target else None,
            "type": target.type if target else None,
        },
        "confidence": _confidence(relationship.confidence),
        "verification_status": relationship.verification_status,
        "source_type": relationship.source_type,
        "source_ref": relationship.source_ref,
        "created_at": _iso(relationship.created_at),
    }


def _timeline_item(event: CaseTimelineEvent, location_index: dict[uuid.UUID, CaseEntity]) -> dict:
    location = location_index.get(event.location_entity_id) if event.location_entity_id else None
    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "occurred_at": _iso(event.occurred_at or event.start_at or event.created_at),
        "occurred_at_precision": event.occurred_at_precision,
        "location": {
            "id": str(location.id),
            "label": location.label,
            "value": location.value,
            "type": location.type,
        } if location else None,
        "confidence": _confidence(event.confidence),
        "verification_status": event.verification_status,
        "source_type": event.source_type,
        "source_ref": event.source_ref,
        "links": [
            {"target_type": link.target_type, "target_id": str(link.target_id)}
            for link in event.links
        ],
    }


def _evidence_item(item: Evidence) -> dict:
    meta = item.meta or {}
    sensitive = bool(meta.get("sensitive")) or item.evidence_type in SENSITIVE_EVIDENCE_TYPES
    return {
        "id": str(item.id),
        "title": item.title,
        "evidence_type": item.evidence_type,
        "source_type": item.source_type,
        "source_url": item.source_url,
        "description": item.description,
        "file_name": item.file_name,
        "file_size": item.file_size,
        "file_mime_type": item.file_mime_type,
        "file_sha256": item.file_sha256,
        "chain_of_custody_status": item.chain_of_custody_status,
        "sensitive": sensitive,
        "tags": item.tags or [],
        "created_at": _iso(item.created_at),
        "links": [
            {"target_type": link.target_type, "target_id": str(link.target_id), "relationship_note": link.relationship_note}
            for link in item.links
        ],
    }


def _location_item(geo: CaseGeolocation, entity_index: dict[uuid.UUID, CaseEntity]) -> dict:
    entity = entity_index.get(geo.target_id) if geo.target_type == "entity" else None
    return {
        "id": str(geo.id),
        "target_type": geo.target_type,
        "target_id": str(geo.target_id),
        "label": geo.label or geo.address_text or (entity.label if entity else "Location observation"),
        "address_text": geo.address_text,
        "latitude": float(geo.latitude),
        "longitude": float(geo.longitude),
        "precision": geo.precision,
        "confidence": _confidence(geo.confidence),
        "verification_status": geo.verification_status,
        "source_type": geo.source_type,
        "source_ref": geo.source_ref,
        "is_primary": geo.is_primary,
        "entity": {
            "id": str(entity.id),
            "type": entity.type,
            "label": entity.label,
            "value": entity.value,
        } if entity else None,
    }


def _scan_item(scan: Scan) -> dict:
    return {
        "id": str(scan.id),
        "seed_value": scan.seed_value,
        "seed_kind": scan.seed_kind,
        "status": scan.status,
        "launch_source": scan.launch_source,
        "source_node_type": scan.source_node_type,
        "source_node_id": str(scan.source_node_id) if scan.source_node_id else None,
        "source_node_label": scan.source_node_label,
        "source_context": scan.source_context or {},
        "modules": scan.modules,
        "progress": scan.progress,
        "total_modules": scan.total_modules,
        "created_at": _iso(scan.created_at),
        "finished_at": _iso(scan.finished_at),
    }


def _lead_item(target_type: str, target_id: uuid.UUID, label: str, lead_type: str, status: str, source_type: str) -> dict:
    return {
        "id": f"{target_type}:{target_id}",
        "target_type": target_type,
        "target_id": str(target_id),
        "label": label,
        "lead_type": lead_type,
        "review_status": status,
        "source_type": source_type,
    }


@router.get("/{case_id}/dossier")
async def get_case_dossier(
    case_id: uuid.UUID,
    include_sensitive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Return a consolidated case dossier for analyst briefing and PI reporting."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    review_result = await db.execute(select(CaseLeadReview).where(CaseLeadReview.case_id == case_id))
    reviews = {(review.target_type, review.target_id): review for review in review_result.scalars().all()}
    rejected_indicators = {
        target_id
        for (target_type, target_id), review in reviews.items()
        if target_type == "indicator" and review.review_status == "rejected"
    }
    rejected_edges = {
        target_id
        for (target_type, target_id), review in reviews.items()
        if target_type == "graph_edge" and review.review_status == "rejected"
    }

    entity_result = await db.execute(
        select(CaseEntity).where(CaseEntity.case_id == case_id).order_by(CaseEntity.created_at)
    )
    entities = entity_result.scalars().all()
    visible_entities = [entity for entity in entities if entity.verification_status != "rejected"]
    confirmed_entities = [entity for entity in visible_entities if entity.verification_status in CONFIRMED_STATUSES]
    entity_index = {entity.id: entity for entity in visible_entities}
    confirmed_entity_index = {entity.id: entity for entity in confirmed_entities}

    relationship_result = await db.execute(
        select(CaseRelationship)
        .where(CaseRelationship.case_id == case_id)
        .order_by(CaseRelationship.created_at)
    )
    relationships = relationship_result.scalars().all()
    confirmed_relationships = [
        rel for rel in relationships
        if (
            rel.verification_status in CONFIRMED_STATUSES
            and (rel.from_node_type != "entity" or rel.from_node_id in confirmed_entity_index)
            and (rel.to_node_type != "entity" or rel.to_node_id in confirmed_entity_index)
        )
    ]

    geo_result = await db.execute(
        select(CaseGeolocation)
        .where(CaseGeolocation.case_id == case_id)
        .order_by(CaseGeolocation.is_primary.desc(), CaseGeolocation.created_at.desc())
    )
    locations = [
        geo for geo in geo_result.scalars().all()
        if (
            geo.verification_status != "rejected"
            and (geo.target_type != "entity" or geo.target_id in entity_index)
        )
    ]
    confirmed_locations = [geo for geo in locations if geo.verification_status in CONFIRMED_STATUSES]

    timeline_result = await db.execute(
        select(CaseTimelineEvent)
        .options(selectinload(CaseTimelineEvent.links))
        .where(CaseTimelineEvent.case_id == case_id)
        .order_by(CaseTimelineEvent.created_at.desc())
    )
    timeline_events = [
        event for event in timeline_result.scalars().unique().all()
        if event.verification_status != "rejected"
    ]
    confirmed_timeline = [event for event in timeline_events if event.verification_status in CONFIRMED_STATUSES]

    evidence_result = await db.execute(
        select(Evidence)
        .options(selectinload(Evidence.links))
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.created_at.desc())
    )
    evidence_items = []
    evidence_activity = []
    sensitive_count = 0
    for item in evidence_result.scalars().unique().all():
        if item.chain_of_custody_status == "rejected":
            continue
        if item.created_at:
            evidence_activity.append(item.created_at)
        evidence = _evidence_item(item)
        if evidence["sensitive"]:
            sensitive_count += 1
            if not include_sensitive:
                continue
        evidence_items.append(evidence)

    scans_result = await db.execute(select(Scan).where(Scan.case_id == case_id).order_by(Scan.created_at.desc()))
    scans = scans_result.scalars().all()

    lead_items: list[dict] = []
    for entity in visible_entities:
        if entity.verification_status in OPEN_LEAD_STATUSES:
            lead_items.append(_lead_item("entity", entity.id, entity.label or entity.value, entity.type, entity.verification_status, entity.source_type))
    for rel in relationships:
        if rel.verification_status in OPEN_LEAD_STATUSES:
            lead_items.append(_lead_item("relationship", rel.id, rel.label or rel.relationship_type, "relationship", rel.verification_status, rel.source_type))
    for event in timeline_events:
        if event.verification_status in OPEN_LEAD_STATUSES:
            lead_items.append(_lead_item("timeline_event", event.id, event.title, event.event_type, event.verification_status, event.source_type))
    for geo in locations:
        if geo.verification_status in OPEN_LEAD_STATUSES:
            lead_items.append(_lead_item("geolocation", geo.id, geo.label or geo.address_text or "Location observation", "geolocation", geo.verification_status, geo.source_type))

    scan_ids = [scan.id for scan in scans]
    scan_edge_rows = []
    indicator_index: dict[uuid.UUID, Indicator] = {}
    if scan_ids:
        edge_result = await db.execute(
            select(Edge, scan_findings.c.scan_id)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(scan_findings.c.scan_id.in_(scan_ids))
        )
        scan_edge_rows = edge_result.all()
        indicator_ids = {edge.src_id for edge, _ in scan_edge_rows} | {edge.dst_id for edge, _ in scan_edge_rows}
        if indicator_ids:
            indicator_result = await db.execute(select(Indicator).where(Indicator.id.in_(list(indicator_ids))))
            indicator_index = {indicator.id: indicator for indicator in indicator_result.scalars().all()}

    indicator_scan_ids: set[uuid.UUID] = set()
    for edge, _ in scan_edge_rows:
        if edge.id not in rejected_edges and edge.src_id not in rejected_indicators and edge.dst_id not in rejected_indicators:
            indicator_scan_ids.add(edge.src_id)
            indicator_scan_ids.add(edge.dst_id)
        edge_review = reviews.get(("graph_edge", edge.id))
        if (edge_review.review_status if edge_review else "needs_review") in OPEN_LEAD_STATUSES:
            lead_items.append(_lead_item("graph_edge", edge.id, edge.relationship_type, "relationship", edge_review.review_status if edge_review else "needs_review", "scan"))

    for indicator_id in indicator_scan_ids:
        review = reviews.get(("indicator", indicator_id))
        status = review.review_status if review else "needs_review"
        if status in OPEN_LEAD_STATUSES:
            indicator = indicator_index.get(indicator_id)
            lead_items.append(_lead_item("indicator", indicator_id, (indicator.label or indicator.value) if indicator else str(indicator_id), indicator.kind if indicator else "indicator", status, "scan"))

    subject_profile_entities = [
        entity for entity in visible_entities
        if (entity.properties or {}).get("subject_profile")
    ]
    subject_candidates = [
        entity for entity in confirmed_entities
        if entity.type in {"person", "alias", "username", "email", "phone", "company", "organization"}
    ]
    if subject_profile_entities:
        subject_candidates = subject_profile_entities
    elif not subject_candidates:
        subject_candidates = confirmed_entities[:3]

    entity_counts = Counter(entity.type for entity in visible_entities)
    relationship_counts = Counter(rel.relationship_type for rel in confirmed_relationships)
    lead_counts = Counter(lead["review_status"] for lead in lead_items)

    return {
        "case": {
            "id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "priority": case.priority,
            "case_type": case.case_type,
            "assigned_to": case.assigned_to,
            "client": case.client,
            "jurisdiction": case.jurisdiction,
            "target_name": case.target_name,
            "target_aliases": case.target_aliases or [],
            "target_location": case.target_location,
            "tags": case.tags or [],
            "created_at": _iso(case.created_at),
            "updated_at": _iso(case.updated_at),
        },
        "subject": {
            "name": case.target_name or (subject_candidates[0].label if subject_candidates else case.title),
            "aliases": case.target_aliases or [entity.value for entity in subject_candidates if entity.type in {"alias", "username"}][:8],
            "location": case.target_location,
            "primary_entities": [_entity_item(entity) for entity in subject_candidates[:6]],
        },
        "summary": {
            "confirmed_entities": len(confirmed_entities),
            "verified_relationships": len(confirmed_relationships),
            "locations": len(locations),
            "timeline_events": len(timeline_events),
            "evidence_items": len(evidence_items),
            "sensitive_evidence_hidden": 0 if include_sensitive else sensitive_count,
            "open_leads": len(lead_items),
            "scans": len(scans),
            "last_activity_at": max(
                [value for value in [
                    case.updated_at,
                    *(scan.created_at for scan in scans),
                    *(event.created_at for event in timeline_events),
                    *evidence_activity,
                ] if value],
                default=datetime.now(timezone.utc),
            ).isoformat(),
        },
        "entities": [_entity_item(entity) for entity in confirmed_entities],
        "relationships": [_relationship_item(rel, entity_index) for rel in confirmed_relationships],
        "locations": [_location_item(geo, entity_index) for geo in (confirmed_locations or locations[:8])],
        "timeline": [_timeline_item(event, entity_index) for event in (confirmed_timeline or timeline_events[:12])],
        "evidence": evidence_items[:24],
        "leads": lead_items[:40],
        "scans": [_scan_item(scan) for scan in scans[:20]],
        "counts": {
            "entities_by_type": dict(entity_counts),
            "relationships_by_type": dict(relationship_counts),
            "leads_by_status": dict(lead_counts),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
