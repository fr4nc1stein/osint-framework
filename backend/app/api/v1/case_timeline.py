"""Case timeline API endpoints."""
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.case import Case
from app.models.case_entity import CaseEntity
from app.models.case_note import CaseNote
from app.models.case_relationship import CaseRelationship
from app.models.case_timeline import CaseTimelineEvent, CaseTimelineLink
from app.models.edge import Edge, scan_findings
from app.models.evidence import Evidence
from app.models.indicator import Indicator
from app.models.scan import Scan
from app.schemas.case_timeline import (
    CaseTimelineEventCreate,
    CaseTimelineEventResponse,
    CaseTimelineEventUpdate,
    CaseTimelineLinkCreate,
    CaseTimelineLinkResponse,
)

router = APIRouter()


async def _ensure_case(case_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(select(Case.id).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")


async def _get_event(case_id: uuid.UUID, event_id: uuid.UUID, db: AsyncSession) -> CaseTimelineEvent:
    result = await db.execute(
        select(CaseTimelineEvent)
        .options(selectinload(CaseTimelineEvent.links))
        .where(CaseTimelineEvent.id == event_id, CaseTimelineEvent.case_id == case_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail=f"Timeline event {event_id} not found")
    return event


async def _target_exists(case_id: uuid.UUID, target_type: str, target_id: uuid.UUID, db: AsyncSession) -> bool:
    if target_type == "case":
        return target_id == case_id

    if target_type == "entity":
        result = await db.execute(select(CaseEntity.id).where(CaseEntity.id == target_id, CaseEntity.case_id == case_id))
        return result.scalar_one_or_none() is not None

    if target_type == "relationship":
        result = await db.execute(
            select(CaseRelationship.id).where(CaseRelationship.id == target_id, CaseRelationship.case_id == case_id)
        )
        return result.scalar_one_or_none() is not None

    if target_type == "evidence":
        result = await db.execute(select(Evidence.id).where(Evidence.id == target_id, Evidence.case_id == case_id))
        return result.scalar_one_or_none() is not None

    if target_type == "scan":
        result = await db.execute(select(Scan.id).where(Scan.id == target_id, Scan.case_id == case_id))
        return result.scalar_one_or_none() is not None

    if target_type == "indicator":
        result = await db.execute(
            select(Indicator.id)
            .select_from(Indicator)
            .join(Edge, or_(Edge.src_id == Indicator.id, Edge.dst_id == Indicator.id))
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .join(Scan, Scan.id == scan_findings.c.scan_id)
            .where(Indicator.id == target_id, Scan.case_id == case_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    if target_type == "graph_edge":
        result = await db.execute(
            select(Edge.id)
            .select_from(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .join(Scan, Scan.id == scan_findings.c.scan_id)
            .where(Edge.id == target_id, Scan.case_id == case_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    if target_type == "note":
        result = await db.execute(select(CaseNote.id).where(CaseNote.id == target_id, CaseNote.case_id == case_id))
        return result.scalar_one_or_none() is not None

    return False


async def _validate_location(case_id: uuid.UUID, location_entity_id: uuid.UUID | None, db: AsyncSession) -> None:
    if not location_entity_id:
        return
    result = await db.execute(
        select(CaseEntity.id).where(CaseEntity.id == location_entity_id, CaseEntity.case_id == case_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="location_entity_id is not a case entity")


async def _create_link(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    link_data: CaseTimelineLinkCreate,
    db: AsyncSession,
) -> CaseTimelineLink:
    if not await _target_exists(case_id, link_data.target_type, link_data.target_id, db):
        raise HTTPException(status_code=400, detail="Timeline link target is not part of this case")
    link = CaseTimelineLink(timeline_event_id=event_id, **link_data.model_dump())
    db.add(link)
    return link


def _with_counts(event: CaseTimelineEvent) -> CaseTimelineEventResponse:
    response = CaseTimelineEventResponse.model_validate(event)
    response.evidence_count = len([link for link in event.links if link.target_type == "evidence"])
    return response


@router.get("/{case_id}/timeline", response_model=List[CaseTimelineEventResponse])
async def list_timeline_events(
    case_id: uuid.UUID,
    target_type: Optional[str] = None,
    target_id: Optional[uuid.UUID] = None,
    event_type: Optional[str] = None,
    verification_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List case timeline events, optionally filtered by linked target."""
    await _ensure_case(case_id, db)
    timeline_time = func.coalesce(CaseTimelineEvent.occurred_at, CaseTimelineEvent.start_at, CaseTimelineEvent.created_at)
    query = (
        select(CaseTimelineEvent)
        .options(selectinload(CaseTimelineEvent.links))
        .where(CaseTimelineEvent.case_id == case_id)
        .order_by(timeline_time.desc(), CaseTimelineEvent.created_at.desc())
    )
    if event_type:
        query = query.where(CaseTimelineEvent.event_type == event_type)
    if verification_status:
        query = query.where(CaseTimelineEvent.verification_status == verification_status)
    if target_type and target_id:
        query = query.join(CaseTimelineLink).where(
            CaseTimelineLink.target_type == target_type,
            CaseTimelineLink.target_id == target_id,
        )
    result = await db.execute(query)
    return [_with_counts(event) for event in result.scalars().unique().all()]


@router.post("/{case_id}/timeline", response_model=CaseTimelineEventResponse, status_code=status.HTTP_201_CREATED)
async def create_timeline_event(
    case_id: uuid.UUID,
    event_data: CaseTimelineEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a manual timeline event."""
    await _ensure_case(case_id, db)
    await _validate_location(case_id, event_data.location_entity_id, db)

    data = event_data.model_dump(exclude={"links"})
    event = CaseTimelineEvent(case_id=case_id, **data)
    db.add(event)
    await db.flush()
    for link_data in event_data.links:
        await _create_link(case_id, event.id, link_data, db)

    await db.commit()
    return _with_counts(await _get_event(case_id, event.id, db))


@router.get("/{case_id}/timeline/{event_id}", response_model=CaseTimelineEventResponse)
async def get_timeline_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single case timeline event."""
    return _with_counts(await _get_event(case_id, event_id, db))


@router.put("/{case_id}/timeline/{event_id}", response_model=CaseTimelineEventResponse)
async def update_timeline_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    event_data: CaseTimelineEventUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a case timeline event."""
    event = await _get_event(case_id, event_id, db)
    update_data = event_data.model_dump(exclude_unset=True)
    await _validate_location(case_id, update_data.get("location_entity_id"), db)

    start_at = update_data.get("start_at", event.start_at)
    end_at = update_data.get("end_at", event.end_at)
    if start_at and end_at and end_at < start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")

    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    return _with_counts(await _get_event(case_id, event_id, db))


@router.delete("/{case_id}/timeline/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeline_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a case timeline event."""
    event = await _get_event(case_id, event_id, db)
    await db.delete(event)
    await db.commit()


@router.post("/{case_id}/timeline/{event_id}/links", response_model=CaseTimelineLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_timeline_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    link_data: CaseTimelineLinkCreate,
    db: AsyncSession = Depends(get_db),
):
    """Link an existing timeline event to a case object."""
    await _get_event(case_id, event_id, db)
    link = await _create_link(case_id, event_id, link_data, db)
    await db.commit()
    await db.refresh(link)
    return link


@router.delete("/{case_id}/timeline/{event_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_timeline_event(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a link from a timeline event."""
    await _get_event(case_id, event_id, db)
    await db.execute(
        delete(CaseTimelineLink).where(
            CaseTimelineLink.id == link_id,
            CaseTimelineLink.timeline_event_id == event_id,
        )
    )
    await db.commit()
