"""Case Graph API — merges all scan graphs in a case"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from app.core.database import get_db
from app.models.case import Case
from app.models.case_timeline import CaseTimelineEvent
from app.models.evidence import Evidence
from app.models.scan import Scan
from app.models.indicator import Indicator
from app.models.edge import Edge, scan_findings
from app.models.case_entity import CaseEntity
from app.models.case_geolocation import CaseGeolocation
from app.models.case_relationship import CaseRelationship
from app.services.case_geolocations import APPROXIMATE_PRECISIONS, LOCATION_KINDS

router = APIRouter()


def _float_or_none(value) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coordinates_from(data: dict | None) -> tuple[float | None, float | None]:
    if not data:
        return None, None
    lat = _float_or_none(data.get("latitude", data.get("lat")))
    lon = _float_or_none(data.get("longitude", data.get("lon", data.get("lng"))))
    if lat is None or lon is None:
        return None, None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, None
    return lat, lon


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _map_bounds(markers: list[dict]) -> dict | None:
    if not markers:
        return None
    lats = [m["latitude"] for m in markers]
    lons = [m["longitude"] for m in markers]
    return {
        "min_latitude": min(lats),
        "max_latitude": max(lats),
        "min_longitude": min(lons),
        "max_longitude": max(lons),
        "center_latitude": sum(lats) / len(lats),
        "center_longitude": sum(lons) / len(lons),
    }


def _entity_marker(
    entity: CaseEntity,
    geolocation: CaseGeolocation | None = None,
    *,
    marker_type: str = "entity",
    context: dict | None = None,
) -> dict | None:
    props = entity.properties or {}
    if geolocation:
        lat = float(geolocation.latitude)
        lon = float(geolocation.longitude)
    else:
        lat, lon = _coordinates_from(props)
    if lat is None or lon is None:
        return None

    precision = (
        geolocation.precision
        if geolocation
        else props.get("precision") or props.get("location_precision") or "unknown"
    )
    source_type = geolocation.source_type if geolocation else entity.source_type
    verification_status = geolocation.verification_status if geolocation else entity.verification_status
    confidence = geolocation.confidence if geolocation and geolocation.confidence is not None else entity.confidence
    can_edit_location = (
        marker_type == "entity"
        and entity.source_type == "manual"
        and (not geolocation or geolocation.source_type == "manual")
    )
    marker = {
        "id": f"{marker_type}:{geolocation.id if geolocation else entity.id}",
        "marker_type": marker_type,
        "target_type": "entity",
        "target_id": str(entity.id),
        "geolocation_id": str(geolocation.id) if geolocation else None,
        "label": (geolocation.label if geolocation else None) or entity.label or entity.value,
        "description": entity.description,
        "entity_type": entity.type,
        "address_text": (geolocation.address_text if geolocation else None) or props.get("address_text") or props.get("address") or entity.value,
        "latitude": lat,
        "longitude": lon,
        "precision": precision,
        "approximate": precision in APPROXIMATE_PRECISIONS,
        "confidence": float(confidence) if confidence is not None else None,
        "verification_status": verification_status,
        "source_type": source_type,
        "source_ref": geolocation.source_ref if geolocation else entity.source_ref,
        "geocoding_source": geolocation.geocoding_source if geolocation else props.get("geocoding_source"),
        "can_edit_location": can_edit_location,
        "created_at": _iso(entity.created_at),
        "updated_at": _iso(geolocation.updated_at if geolocation else entity.updated_at),
        "properties": {**props, **({"geolocation": geolocation.meta or {}} if geolocation else {})},
        "links": [{"target_type": "entity", "target_id": str(entity.id), "label": entity.label or entity.value}],
    }
    if context:
        marker.update(context)
    return marker


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

    scan_ids = [s.id for s in scans]
    scan_index = {s.id: {"id": str(s.id), "seed_value": s.seed_value, "seed_kind": s.seed_kind} for s in scans}

    # Build edge map and collect indicator ids, tracking which scans each edge appears in
    edge_map: dict[uuid.UUID, dict] = {}
    indicator_scan_map: dict[uuid.UUID, set] = {}

    if scan_ids:
        # Fetch all edges across all scans
        result = await db.execute(
            select(Edge, scan_findings.c.scan_id)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(scan_findings.c.scan_id.in_(scan_ids))
        )
        rows = result.all()

        for edge, scan_id in rows:
            if edge.id not in edge_map:
                edge_map[edge.id] = {
                    "id": str(edge.id),
                    "source": str(edge.src_id),
                    "target": str(edge.dst_id),
                    "relationship": edge.relationship_type,
                    "confidence": float(edge.confidence),
                    "source_module": edge.source_module,
                    "source_type": "scan",
                    "verification_status": "confirmed",
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
            "graph_node_type": "indicator",
            "kind": ind.kind,
            "value": ind.value,
            "label": ind.label,
            "meta": ind.meta or {},
            "confidence": float(ind.confidence) if ind.confidence else None,
            "source_type": "scan",
            "verification_status": "confirmed",
            "scan_origins": [scan_index[sid]["seed_value"] for sid in indicator_scan_map.get(ind.id, [])],
        }
        for ind in indicators
    ]

    result = await db.execute(
        select(CaseEntity).where(CaseEntity.case_id == case_id).order_by(CaseEntity.created_at)
    )
    manual_entities = result.scalars().all()
    nodes.extend(
        {
            "id": str(entity.id),
            "graph_node_type": "entity",
            "kind": entity.type,
            "value": entity.value,
            "label": entity.label,
            "meta": entity.properties or {},
            "description": entity.description,
            "confidence": float(entity.confidence) if entity.confidence is not None else None,
            "source_type": entity.source_type,
            "source_ref": entity.source_ref,
            "verification_status": entity.verification_status,
            "visibility": entity.visibility,
            "created_by": entity.created_by,
            "scan_origins": [],
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat(),
        }
        for entity in manual_entities
    )

    result = await db.execute(
        select(CaseRelationship)
        .where(CaseRelationship.case_id == case_id)
        .order_by(CaseRelationship.created_at)
    )
    manual_edges = [
        {
            "id": str(rel.id),
            "source": str(rel.from_node_id),
            "target": str(rel.to_node_id),
            "relationship": rel.relationship_type,
            "label": rel.label,
            "description": rel.description,
            "confidence": float(rel.confidence) if rel.confidence is not None else None,
            "source_module": "manual",
            "source_type": rel.source_type,
            "verification_status": rel.verification_status,
            "properties": rel.properties or {},
            "scan_origins": [],
            "created_at": rel.created_at.isoformat(),
            "updated_at": rel.updated_at.isoformat(),
        }
        for rel in result.scalars().all()
    ]

    return {
        "nodes": nodes,
        "edges": [*edge_map.values(), *manual_edges],
        "scans": [
            {"id": str(s.id), "seed_value": s.seed_value, "seed_kind": s.seed_kind, "status": s.status}
            for s in scans
        ],
        "manual_counts": {
            "entities": len(manual_entities),
            "relationships": len(manual_edges),
        },
    }


@router.get("/{case_id}/map")
async def get_case_map(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Return normalized map markers for a case without exposing map provider details."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    markers: list[dict] = []
    unmapped: list[dict] = []
    warnings: list[str] = []

    result = await db.execute(
        select(CaseEntity).where(CaseEntity.case_id == case_id).order_by(CaseEntity.created_at)
    )
    entities = result.scalars().all()
    entity_index = {entity.id: entity for entity in entities}

    result = await db.execute(
        select(CaseGeolocation)
        .where(CaseGeolocation.case_id == case_id)
        .order_by(CaseGeolocation.is_primary.desc(), CaseGeolocation.created_at.desc())
    )
    geolocations = result.scalars().all()
    primary_entity_geos: dict[uuid.UUID, CaseGeolocation] = {}
    extra_entity_geos: list[CaseGeolocation] = []
    for geo in geolocations:
        if geo.target_type != "entity":
            continue
        if geo.is_primary and geo.target_id not in primary_entity_geos:
            primary_entity_geos[geo.target_id] = geo
        else:
            extra_entity_geos.append(geo)

    for entity in entities:
        marker = _entity_marker(entity, primary_entity_geos.get(entity.id))
        if marker:
            markers.append(marker)
        elif entity.type in LOCATION_KINDS:
            unmapped.append({
                "target_type": "entity",
                "target_id": str(entity.id),
                "label": entity.label or entity.value,
                "entity_type": entity.type,
                "reason": "missing_coordinates",
                "source_type": entity.source_type,
                "verification_status": entity.verification_status,
            })

    for geo in extra_entity_geos:
        entity = entity_index.get(geo.target_id)
        if not entity:
            continue
        marker = _entity_marker(
            entity,
            geo,
            marker_type="geolocation",
            context={
                "links": [
                    {"target_type": "entity", "target_id": str(entity.id), "label": entity.label or entity.value},
                    {"target_type": "geolocation", "target_id": str(geo.id), "label": geo.label or geo.address_text},
                ],
            },
        )
        if marker:
            markers.append(marker)

    result = await db.execute(
        select(Evidence)
        .options(selectinload(Evidence.links))
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.created_at)
    )
    evidence_items = result.scalars().unique().all()
    for item in evidence_items:
        lat, lon = _coordinates_from(item.meta or {})
        if lat is not None and lon is not None:
            precision = (item.meta or {}).get("precision") or "unknown"
            markers.append({
                "id": f"evidence:{item.id}",
                "marker_type": "evidence",
                "target_type": "evidence",
                "target_id": str(item.id),
                "label": item.title,
                "description": item.description,
                "entity_type": item.evidence_type,
                "address_text": (item.meta or {}).get("address_text") or item.source_url,
                "latitude": lat,
                "longitude": lon,
                "precision": precision,
                "approximate": precision in {"city", "region", "country", "ip_geo_approximate", "unknown"},
                "confidence": None,
                "verification_status": item.chain_of_custody_status,
                "source_type": item.source_type,
                "source_ref": item.source_url,
                "geolocation_id": None,
                "geocoding_source": (item.meta or {}).get("geocoding_source"),
                "can_edit_location": False,
                "created_at": _iso(item.created_at),
                "updated_at": _iso(item.updated_at),
                "properties": item.meta or {},
                "links": [
                    {"target_type": "evidence", "target_id": str(item.id), "label": item.title},
                    *[
                        {"target_type": link.target_type, "target_id": str(link.target_id), "label": link.relationship_note}
                        for link in item.links
                    ],
                ],
            })
        elif item.evidence_type == "map_location":
            unmapped.append({
                "target_type": "evidence",
                "target_id": str(item.id),
                "label": item.title,
                "entity_type": item.evidence_type,
                "reason": "missing_coordinates",
                "source_type": item.source_type,
                "verification_status": item.chain_of_custody_status,
            })

    result = await db.execute(
        select(CaseTimelineEvent)
        .options(selectinload(CaseTimelineEvent.links))
        .where(CaseTimelineEvent.case_id == case_id)
        .order_by(CaseTimelineEvent.created_at)
    )
    timeline_events = result.scalars().unique().all()
    for event in timeline_events:
        if not event.location_entity_id:
            continue
        entity = entity_index.get(event.location_entity_id)
        if not entity:
            unmapped.append({
                "target_type": "timeline_event",
                "target_id": str(event.id),
                "label": event.title,
                "entity_type": event.event_type,
                "reason": "missing_location_entity",
                "source_type": event.source_type,
                "verification_status": event.verification_status,
            })
            continue
        marker = _entity_marker(
            entity,
            primary_entity_geos.get(entity.id),
            marker_type="timeline_event",
            context={
                "id": f"timeline_event:{event.id}",
                "target_type": "timeline_event",
                "target_id": str(event.id),
                "label": event.title,
                "description": event.description,
                "entity_type": event.event_type,
                "confidence": float(event.confidence) if event.confidence is not None else None,
                "verification_status": event.verification_status,
                "source_type": event.source_type,
                "source_ref": event.source_ref,
                "can_edit_location": False,
                "occurred_at": _iso(event.occurred_at or event.start_at),
                "links": [
                    {"target_type": "timeline_event", "target_id": str(event.id), "label": event.title},
                    {"target_type": "entity", "target_id": str(entity.id), "label": entity.label or entity.value},
                    *[
                        {"target_type": link.target_type, "target_id": str(link.target_id), "label": None}
                        for link in event.links
                    ],
                ],
            },
        )
        if marker:
            markers.append(marker)
        else:
            unmapped.append({
                "target_type": "timeline_event",
                "target_id": str(event.id),
                "label": event.title,
                "entity_type": event.event_type,
                "reason": "location_entity_missing_coordinates",
                "source_type": event.source_type,
                "verification_status": event.verification_status,
            })

    result = await db.execute(
        select(Scan).where(Scan.case_id == case_id).order_by(Scan.created_at)
    )
    scans = result.scalars().all()
    scan_ids = [scan.id for scan in scans]
    scan_index = {scan.id: scan for scan in scans}

    if scan_ids:
        result = await db.execute(
            select(Edge, scan_findings.c.scan_id)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(scan_findings.c.scan_id.in_(scan_ids))
        )
        edge_rows = result.all()
        indicator_ids = {edge.src_id for edge, _ in edge_rows} | {edge.dst_id for edge, _ in edge_rows}
        if indicator_ids:
            result = await db.execute(select(Indicator).where(Indicator.id.in_(list(indicator_ids))))
            indicator_index = {indicator.id: indicator for indicator in result.scalars().all()}
        else:
            indicator_index = {}

        seen_scan_markers: set[tuple[str, str, float, float]] = set()
        for edge, scan_id in edge_rows:
            lat, lon = _coordinates_from(edge.evidence or {})
            if lat is None or lon is None:
                continue
            scan = scan_index.get(scan_id)
            dst = indicator_index.get(edge.dst_id)
            src = indicator_index.get(edge.src_id)
            label = dst.value if dst and dst.kind in {"location", "address"} else None
            label = label or (edge.evidence or {}).get("city") or (edge.evidence or {}).get("country") or "Scan location"
            marker_key = (str(edge.id), str(scan_id), lat, lon)
            if marker_key in seen_scan_markers:
                continue
            seen_scan_markers.add(marker_key)
            markers.append({
                "id": f"scan:{scan_id}:edge:{edge.id}",
                "marker_type": "scan",
                "target_type": "graph_edge",
                "target_id": str(edge.id),
                "label": label,
                "description": f"{src.value if src else 'scan result'} {edge.relationship_type.replace('_', ' ')} {dst.value if dst else label}",
                "entity_type": dst.kind if dst else "location",
                "address_text": label,
                "latitude": lat,
                "longitude": lon,
                "precision": "ip_geo_approximate" if edge.source_module == "ip_geolocation" else "unknown",
                "approximate": True,
                "confidence": float(edge.confidence) if edge.confidence is not None else None,
                "verification_status": "needs_review",
                "source_type": "scan",
                "source_module": edge.source_module,
                "source_ref": scan.seed_value if scan else None,
                "geolocation_id": None,
                "geocoding_source": None,
                "can_edit_location": False,
                "created_at": _iso(edge.created_at),
                "properties": edge.evidence or {},
                "links": [
                    {"target_type": "scan", "target_id": str(scan_id), "label": scan.seed_value if scan else None},
                    {"target_type": "graph_edge", "target_id": str(edge.id), "label": edge.relationship_type},
                ],
            })
            if edge.source_module == "ip_geolocation":
                warnings.append("IP geolocation markers are approximate and should not be treated as confirmed physical presence.")

    markers.sort(key=lambda marker: (marker.get("source_type") != "manual", marker["label"]))
    warnings = sorted(set(warnings))

    return {
        "markers": markers,
        "unmapped": unmapped,
        "bounds": _map_bounds(markers),
        "warnings": warnings,
        "counts": {
            "markers": len(markers),
            "manual": len([m for m in markers if m["source_type"] == "manual"]),
            "scan": len([m for m in markers if m["source_type"] == "scan"]),
            "evidence": len([m for m in markers if m["marker_type"] == "evidence"]),
            "timeline": len([m for m in markers if m["marker_type"] == "timeline_event"]),
            "unmapped": len(unmapped),
        },
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
