"""Case geolocation API endpoints."""
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.case import Case
from app.models.case_entity import CaseEntity
from app.models.case_geolocation import CaseGeolocation
from app.schemas.case_geolocation import (
    CaseGeolocationCreate,
    CaseGeolocationResponse,
    CaseGeolocationUpdate,
    GeocodeRequest,
    GeocodeResult,
)
from app.services.case_geolocations import mirror_geolocation_to_entity_properties, set_primary_for_target
from app.services.geocoding import geocode_address

router = APIRouter()


async def _ensure_case(case_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(select(Case.id).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")


async def _get_entity_target(case_id: uuid.UUID, target_id: uuid.UUID, db: AsyncSession) -> CaseEntity | None:
    result = await db.execute(
        select(CaseEntity).where(CaseEntity.id == target_id, CaseEntity.case_id == case_id)
    )
    return result.scalar_one_or_none()


async def _ensure_supported_target(case_id: uuid.UUID, target_type: str, target_id: uuid.UUID, db: AsyncSession) -> CaseEntity | None:
    if target_type == "entity":
        entity = await _get_entity_target(case_id, target_id, db)
        if not entity:
            raise HTTPException(status_code=400, detail="Entity target is not part of this case")
        if entity.source_type != "manual":
            raise HTTPException(status_code=403, detail="Only manual entities can receive editable geolocation observations")
        return entity
    raise HTTPException(status_code=400, detail="Editable geolocation observations currently support entity targets only")


@router.get("/{case_id}/geolocations", response_model=List[CaseGeolocationResponse])
async def list_geolocations(
    case_id: uuid.UUID,
    target_type: str | None = Query(default=None),
    target_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """List normalized geolocation observations for a case."""
    await _ensure_case(case_id, db)
    stmt = select(CaseGeolocation).where(CaseGeolocation.case_id == case_id)
    if target_type:
        stmt = stmt.where(CaseGeolocation.target_type == target_type)
    if target_id:
        stmt = stmt.where(CaseGeolocation.target_id == target_id)
    result = await db.execute(stmt.order_by(CaseGeolocation.is_primary.desc(), CaseGeolocation.created_at.desc()))
    return result.scalars().all()


@router.post("/{case_id}/geolocations", response_model=CaseGeolocationResponse, status_code=status.HTTP_201_CREATED)
async def create_geolocation(
    case_id: uuid.UUID,
    body: CaseGeolocationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a manual geolocation observation for a case object."""
    await _ensure_case(case_id, db)
    entity = await _ensure_supported_target(case_id, body.target_type, body.target_id, db)

    geo = CaseGeolocation(case_id=case_id, **body.model_dump())
    db.add(geo)
    await db.flush()
    if geo.is_primary:
        await set_primary_for_target(db, case_id, geo.target_type, geo.target_id, geo.id)
        mirror_geolocation_to_entity_properties(entity, geo)

    await db.commit()
    await db.refresh(geo)
    return geo


@router.put("/{case_id}/geolocations/{geolocation_id}", response_model=CaseGeolocationResponse)
async def update_geolocation(
    case_id: uuid.UUID,
    geolocation_id: uuid.UUID,
    body: CaseGeolocationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a normalized geolocation observation."""
    result = await db.execute(
        select(CaseGeolocation).where(CaseGeolocation.id == geolocation_id, CaseGeolocation.case_id == case_id)
    )
    geo = result.scalar_one_or_none()
    if not geo:
        raise HTTPException(status_code=404, detail=f"Geolocation {geolocation_id} not found")
    entity = await _ensure_supported_target(case_id, geo.target_type, geo.target_id, db)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(geo, field, value)

    if geo.is_primary:
        await set_primary_for_target(db, case_id, geo.target_type, geo.target_id, geo.id)
        mirror_geolocation_to_entity_properties(entity, geo)

    await db.commit()
    await db.refresh(geo)
    return geo


@router.delete("/{case_id}/geolocations/{geolocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_geolocation(
    case_id: uuid.UUID,
    geolocation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a manual geolocation observation."""
    result = await db.execute(
        select(CaseGeolocation).where(CaseGeolocation.id == geolocation_id, CaseGeolocation.case_id == case_id)
    )
    geo = result.scalar_one_or_none()
    if not geo:
        raise HTTPException(status_code=404, detail=f"Geolocation {geolocation_id} not found")
    if geo.source_type != "manual":
        raise HTTPException(status_code=403, detail="Non-manual geolocation observations are read-only")
    await db.delete(geo)
    await db.commit()


@router.post("/{case_id}/geocode", response_model=List[GeocodeResult])
async def geocode_case_address(
    case_id: uuid.UUID,
    body: GeocodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Geocode an address only after explicit external-submission consent."""
    await _ensure_case(case_id, db)
    if not body.consent_to_external_lookup:
        raise HTTPException(
            status_code=400,
            detail="Geocoding sends the query to an external provider. Set consent_to_external_lookup=true to continue.",
        )
    results = await geocode_address(body.provider, body.query, body.limit, db)
    if not results:
        raise HTTPException(status_code=422, detail=f"{body.provider} geocoding is not configured or returned no results")
    return results
