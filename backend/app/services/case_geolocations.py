"""Helpers for case geolocation observations."""
from __future__ import annotations

from typing import Any
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_entity import CaseEntity
from app.models.case_geolocation import CaseGeolocation


LOCATION_KINDS = {"address", "location", "office", "company", "organization", "person", "vehicle"}
APPROXIMATE_PRECISIONS = {"city", "region", "country", "ip_geo_approximate", "unknown"}


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def coordinates_from(data: dict | None) -> tuple[float | None, float | None]:
    if not data:
        return None, None
    lat = float_or_none(data.get("latitude", data.get("lat")))
    lon = float_or_none(data.get("longitude", data.get("lon", data.get("lng"))))
    if lat is None or lon is None:
        return None, None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, None
    return lat, lon


def entity_location_payload(entity: CaseEntity) -> dict | None:
    if entity.type not in LOCATION_KINDS:
        return None
    props = entity.properties or {}
    lat, lon = coordinates_from(props)
    if lat is None or lon is None:
        return None
    return {
        "label": props.get("map_label") or entity.label or entity.value,
        "address_text": props.get("address_text") or props.get("address") or entity.value,
        "latitude": lat,
        "longitude": lon,
        "precision": props.get("location_precision") or props.get("precision") or "unknown",
        "geocoding_source": props.get("geocoding_source"),
        "confidence": float(entity.confidence) if entity.confidence is not None else None,
        "verification_status": entity.verification_status,
        "source_type": entity.source_type,
        "source_ref": entity.source_ref,
        "notes": props.get("location_note"),
        "created_by": entity.created_by,
        "meta": {
            "legacy_entity_properties": True,
        },
    }


async def set_primary_for_target(
    db: AsyncSession,
    case_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID,
    active_id: uuid.UUID | None = None,
) -> None:
    stmt = (
        update(CaseGeolocation)
        .where(CaseGeolocation.case_id == case_id)
        .where(CaseGeolocation.target_type == target_type)
        .where(CaseGeolocation.target_id == target_id)
        .where(CaseGeolocation.id != active_id)
        .values(is_primary=False)
    )
    await db.execute(stmt)


async def upsert_entity_primary_geolocation(db: AsyncSession, entity: CaseEntity) -> CaseGeolocation | None:
    payload = entity_location_payload(entity)
    if not payload:
        return None

    result = await db.execute(
        select(CaseGeolocation)
        .where(CaseGeolocation.case_id == entity.case_id)
        .where(CaseGeolocation.target_type == "entity")
        .where(CaseGeolocation.target_id == entity.id)
        .where(CaseGeolocation.is_primary == True)
        .order_by(CaseGeolocation.created_at.desc())
        .limit(1)
    )
    geo = result.scalar_one_or_none()
    if not geo:
        geo = CaseGeolocation(
            case_id=entity.case_id,
            target_type="entity",
            target_id=entity.id,
            is_primary=True,
            **payload,
        )
        db.add(geo)
        await db.flush()
        return geo

    for field, value in payload.items():
        setattr(geo, field, value)
    await db.flush()
    return geo


def mirror_geolocation_to_entity_properties(entity: CaseEntity, geo: CaseGeolocation) -> None:
    props = dict(entity.properties or {})
    props["address_text"] = geo.address_text or entity.value
    props["latitude"] = float(geo.latitude)
    props["longitude"] = float(geo.longitude)
    props["location_precision"] = geo.precision
    props["geocoding_source"] = geo.geocoding_source
    if geo.notes:
        props["location_note"] = geo.notes
    else:
        props.pop("location_note", None)
    entity.properties = props
    entity.confidence = geo.confidence
    entity.verification_status = geo.verification_status
