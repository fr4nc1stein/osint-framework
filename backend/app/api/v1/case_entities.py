"""Manual case entities and relationships API endpoints."""
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.case import Case
from app.models.case_entity import CaseEntity
from app.models.case_geolocation import CaseGeolocation
from app.models.case_relationship import CaseRelationship
from app.models.edge import Edge, scan_findings
from app.models.indicator import Indicator
from app.models.scan import Scan
from app.schemas.case_entity import CaseEntityCreate, CaseEntityResponse, CaseEntityUpdate
from app.schemas.case_relationship import (
    CaseRelationshipCreate,
    CaseRelationshipResponse,
    CaseRelationshipUpdate,
)
from app.services.case_geolocations import upsert_entity_primary_geolocation

router = APIRouter()


async def _ensure_case(case_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(select(Case.id).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")


async def _node_exists(
    case_id: uuid.UUID,
    node_type: str,
    node_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    if node_type == "entity":
        result = await db.execute(
            select(CaseEntity.id).where(CaseEntity.id == node_id, CaseEntity.case_id == case_id)
        )
        return result.scalar_one_or_none() is not None

    if node_type == "indicator":
        result = await db.execute(
            select(Indicator.id)
            .select_from(Indicator)
            .join(Edge, or_(Edge.src_id == Indicator.id, Edge.dst_id == Indicator.id))
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .join(Scan, Scan.id == scan_findings.c.scan_id)
            .where(Indicator.id == node_id, Scan.case_id == case_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    return False


async def _validate_relationship_nodes(
    case_id: uuid.UUID,
    data: CaseRelationshipCreate,
    db: AsyncSession,
) -> None:
    if data.from_node_id == data.to_node_id:
        raise HTTPException(status_code=400, detail="Source and target must be different nodes")
    from_exists = await _node_exists(case_id, data.from_node_type, data.from_node_id, db)
    to_exists = await _node_exists(case_id, data.to_node_type, data.to_node_id, db)
    if not from_exists:
        raise HTTPException(status_code=400, detail="Source node is not part of this case graph")
    if not to_exists:
        raise HTTPException(status_code=400, detail="Target node is not part of this case graph")


@router.get("/{case_id}/entities", response_model=List[CaseEntityResponse])
async def list_entities(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List manual case entities."""
    await _ensure_case(case_id, db)
    result = await db.execute(
        select(CaseEntity).where(CaseEntity.case_id == case_id).order_by(CaseEntity.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{case_id}/entities", response_model=CaseEntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    case_id: uuid.UUID,
    entity_data: CaseEntityCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a manual case entity, optionally connected to an existing graph node."""
    await _ensure_case(case_id, db)

    data = entity_data.model_dump(
        exclude={
            "connected_to_node_type",
            "connected_to_node_id",
            "relationship_type",
            "relationship_label",
        }
    )
    entity = CaseEntity(case_id=case_id, **data)
    db.add(entity)
    await db.flush()
    await upsert_entity_primary_geolocation(db, entity)

    has_connected_node = bool(entity_data.connected_to_node_type and entity_data.connected_to_node_id)
    if entity_data.relationship_type and not has_connected_node:
        raise HTTPException(status_code=400, detail="relationship_type requires connected_to_node_type and connected_to_node_id")

    if has_connected_node:
        exists = await _node_exists(
            case_id,
            entity_data.connected_to_node_type,
            entity_data.connected_to_node_id,
            db,
        )
        if not exists:
            raise HTTPException(status_code=400, detail="Connected node is not part of this case graph")

        relationship = CaseRelationship(
            case_id=case_id,
            from_node_type=entity_data.connected_to_node_type,
            from_node_id=entity_data.connected_to_node_id,
            to_node_type="entity",
            to_node_id=entity.id,
            relationship_type=entity_data.relationship_type or "associated_with",
            label=entity_data.relationship_label,
            source_type="manual",
            confidence=entity_data.confidence,
            verification_status=entity_data.verification_status,
            created_by=entity_data.created_by,
        )
        db.add(relationship)

    await db.commit()
    await db.refresh(entity)
    return entity


@router.put("/{case_id}/entities/{entity_id}", response_model=CaseEntityResponse)
async def update_entity(
    case_id: uuid.UUID,
    entity_id: uuid.UUID,
    entity_data: CaseEntityUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a manual case entity."""
    result = await db.execute(
        select(CaseEntity).where(CaseEntity.id == entity_id, CaseEntity.case_id == case_id)
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    for field, value in entity_data.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)
    await upsert_entity_primary_geolocation(db, entity)

    await db.commit()
    await db.refresh(entity)
    return entity


@router.delete("/{case_id}/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    case_id: uuid.UUID,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a manual case entity and its manual relationships."""
    result = await db.execute(
        select(CaseEntity).where(CaseEntity.id == entity_id, CaseEntity.case_id == case_id)
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    await db.execute(
        delete(CaseRelationship).where(
            CaseRelationship.case_id == case_id,
            or_(
                (CaseRelationship.from_node_type == "entity") & (CaseRelationship.from_node_id == entity_id),
                (CaseRelationship.to_node_type == "entity") & (CaseRelationship.to_node_id == entity_id),
            ),
        )
    )
    await db.execute(
        delete(CaseGeolocation).where(
            CaseGeolocation.case_id == case_id,
            CaseGeolocation.target_type == "entity",
            CaseGeolocation.target_id == entity_id,
        )
    )
    await db.delete(entity)
    await db.commit()


@router.get("/{case_id}/relationships", response_model=List[CaseRelationshipResponse])
async def list_relationships(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List manual case relationships."""
    await _ensure_case(case_id, db)
    result = await db.execute(
        select(CaseRelationship)
        .where(CaseRelationship.case_id == case_id)
        .order_by(CaseRelationship.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{case_id}/relationships", response_model=CaseRelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    case_id: uuid.UUID,
    relationship_data: CaseRelationshipCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a manual relationship between two case graph nodes."""
    await _ensure_case(case_id, db)
    await _validate_relationship_nodes(case_id, relationship_data, db)

    relationship = CaseRelationship(case_id=case_id, **relationship_data.model_dump())
    db.add(relationship)
    await db.commit()
    await db.refresh(relationship)
    return relationship


@router.put("/{case_id}/relationships/{relationship_id}", response_model=CaseRelationshipResponse)
async def update_relationship(
    case_id: uuid.UUID,
    relationship_id: uuid.UUID,
    relationship_data: CaseRelationshipUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a manual case relationship."""
    result = await db.execute(
        select(CaseRelationship).where(
            CaseRelationship.id == relationship_id,
            CaseRelationship.case_id == case_id,
        )
    )
    relationship = result.scalar_one_or_none()
    if not relationship:
        raise HTTPException(status_code=404, detail=f"Relationship {relationship_id} not found")

    for field, value in relationship_data.model_dump(exclude_unset=True).items():
        setattr(relationship, field, value)

    await db.commit()
    await db.refresh(relationship)
    return relationship


@router.delete("/{case_id}/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    case_id: uuid.UUID,
    relationship_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a manual case relationship."""
    result = await db.execute(
        select(CaseRelationship).where(
            CaseRelationship.id == relationship_id,
            CaseRelationship.case_id == case_id,
        )
    )
    relationship = result.scalar_one_or_none()
    if not relationship:
        raise HTTPException(status_code=404, detail=f"Relationship {relationship_id} not found")
    await db.delete(relationship)
    await db.commit()
