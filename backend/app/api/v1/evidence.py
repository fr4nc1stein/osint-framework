"""Case evidence API endpoints."""
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.case import Case
from app.models.case_entity import CaseEntity
from app.models.case_relationship import CaseRelationship
from app.models.case_note import CaseNote
from app.models.edge import Edge, scan_findings
from app.models.evidence import Evidence, EvidenceLink
from app.models.indicator import Indicator
from app.models.report import Report
from app.models.scan import Scan
from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceLinkCreate,
    EvidenceLinkResponse,
    EvidenceResponse,
)
from app.services.evidence_storage import EvidenceStorageService, get_evidence_storage

router = APIRouter()

VALID_EVIDENCE_TYPES = {
    "note",
    "url",
    "screenshot",
    "image",
    "document",
    "pdf",
    "text",
    "scan_result",
    "api_response",
    "map_location",
    "analyst_observation",
}
VALID_SOURCE_TYPES = {"manual", "scan", "integration", "import", "ai_suggested"}


async def _ensure_case(case_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(select(Case.id).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")


async def _get_evidence(case_id: uuid.UUID, evidence_id: uuid.UUID, db: AsyncSession) -> Evidence:
    result = await db.execute(
        select(Evidence)
        .options(selectinload(Evidence.links))
        .where(Evidence.id == evidence_id, Evidence.case_id == case_id)
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found")
    return evidence


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

    if target_type == "scan":
        result = await db.execute(select(Scan.id).where(Scan.id == target_id, Scan.case_id == case_id))
        return result.scalar_one_or_none() is not None

    if target_type in {"indicator", "finding", "graph_edge"}:
        if target_type == "indicator":
            query = (
                select(Indicator.id)
                .select_from(Indicator)
                .join(Edge, or_(Edge.src_id == Indicator.id, Edge.dst_id == Indicator.id))
                .join(scan_findings, Edge.id == scan_findings.c.edge_id)
                .join(Scan, Scan.id == scan_findings.c.scan_id)
                .where(Indicator.id == target_id, Scan.case_id == case_id)
                .limit(1)
            )
        else:
            query = (
                select(Edge.id)
                .select_from(Edge)
                .join(scan_findings, Edge.id == scan_findings.c.edge_id)
                .join(Scan, Scan.id == scan_findings.c.scan_id)
                .where(Edge.id == target_id, Scan.case_id == case_id)
                .limit(1)
            )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    if target_type == "report":
        result = await db.execute(select(Report.id).where(Report.id == target_id, Report.case_id == case_id))
        return result.scalar_one_or_none() is not None

    if target_type == "note":
        result = await db.execute(select(CaseNote.id).where(CaseNote.id == target_id, CaseNote.case_id == case_id))
        return result.scalar_one_or_none() is not None

    if target_type == "timeline_event":
        return False

    return False


async def _create_link(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    link_data: EvidenceLinkCreate,
    db: AsyncSession,
) -> EvidenceLink:
    if not await _target_exists(case_id, link_data.target_type, link_data.target_id, db):
        raise HTTPException(status_code=400, detail="Evidence target is not part of this case")
    link = EvidenceLink(evidence_id=evidence_id, **link_data.model_dump())
    db.add(link)
    return link


def _with_urls(evidence: Evidence) -> EvidenceResponse:
    response = EvidenceResponse.model_validate(evidence)
    base = f"/api/v1/cases/{evidence.case_id}/evidence/{evidence.id}"
    if evidence.storage_key:
        response.download_url = f"{base}/download"
        response.preview_url = f"{base}/preview"
    if evidence.thumbnail_storage_key:
        response.thumbnail_url = f"{base}/thumbnail"
    return response


@router.get("/{case_id}/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    case_id: uuid.UUID,
    target_type: Optional[str] = None,
    target_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """List evidence for a case or for a specific linked target."""
    await _ensure_case(case_id, db)
    query = (
        select(Evidence)
        .options(selectinload(Evidence.links))
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.created_at.desc())
    )
    if target_type and target_id:
        query = query.join(EvidenceLink).where(
            EvidenceLink.target_type == target_type,
            EvidenceLink.target_id == target_id,
        )
    result = await db.execute(query)
    return [_with_urls(evidence) for evidence in result.scalars().unique().all()]


@router.post("/{case_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def create_text_evidence(
    case_id: uuid.UUID,
    evidence_data: EvidenceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create URL, note, or observation evidence without a file upload."""
    await _ensure_case(case_id, db)
    evidence = Evidence(
        case_id=case_id,
        title=evidence_data.title,
        description=evidence_data.description,
        evidence_type=evidence_data.evidence_type,
        source_type=evidence_data.source_type,
        source_url=evidence_data.source_url,
        captured_at=evidence_data.captured_at,
        collected_by=evidence_data.collected_by,
        chain_of_custody_status=evidence_data.chain_of_custody_status,
        meta=evidence_data.metadata,
    )
    db.add(evidence)
    await db.flush()
    if evidence_data.link:
        await _create_link(case_id, evidence.id, evidence_data.link, db)
    await db.commit()
    return _with_urls(await _get_evidence(case_id, evidence.id, db))


@router.post("/{case_id}/evidence/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: uuid.UUID,
    title: str = Form(...),
    evidence_type: str = Form("document"),
    source_type: str = Form("manual"),
    description: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    captured_at: Optional[datetime] = Form(None),
    collected_by: Optional[str] = Form(None),
    chain_of_custody_status: str = Form("collected"),
    target_type: Optional[str] = Form(None),
    target_id: Optional[uuid.UUID] = Form(None),
    relationship_note: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: EvidenceStorageService = Depends(get_evidence_storage),
):
    """Upload an evidence file through the backend and store it in MinIO."""
    await _ensure_case(case_id, db)
    if evidence_type not in VALID_EVIDENCE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported evidence_type")
    if source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported source_type")
    if target_type or target_id:
        if not target_type or not target_id:
            raise HTTPException(status_code=400, detail="target_type and target_id must be provided together")
        if not await _target_exists(case_id, target_type, target_id, db):
            raise HTTPException(status_code=400, detail="Evidence target is not part of this case")

    evidence = Evidence(
        case_id=case_id,
        title=title,
        description=description,
        evidence_type=evidence_type,
        source_type=source_type,
        source_url=source_url,
        captured_at=captured_at,
        collected_by=collected_by,
        chain_of_custody_status=chain_of_custody_status,
    )
    db.add(evidence)
    await db.flush()

    stored = await storage.save_upload(case_id, evidence.id, file)
    evidence.file_name = stored.file_name
    evidence.file_mime_type = stored.file_mime_type
    evidence.file_size = stored.file_size
    evidence.file_sha256 = stored.file_sha256
    evidence.file_hash = stored.file_sha256
    evidence.storage_backend = stored.storage_backend
    evidence.storage_key = stored.storage_key
    evidence.thumbnail_storage_key = stored.thumbnail_storage_key

    if target_type and target_id:
        await _create_link(
            case_id,
            evidence.id,
            EvidenceLinkCreate(target_type=target_type, target_id=target_id, relationship_note=relationship_note),
            db,
        )

    await db.commit()
    return _with_urls(await _get_evidence(case_id, evidence.id, db))


@router.get("/{case_id}/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get one evidence record."""
    return _with_urls(await _get_evidence(case_id, evidence_id, db))


@router.post("/{case_id}/evidence/{evidence_id}/links", response_model=EvidenceLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    link_data: EvidenceLinkCreate,
    db: AsyncSession = Depends(get_db),
):
    """Attach an existing evidence item to another case object."""
    await _get_evidence(case_id, evidence_id, db)
    link = await _create_link(case_id, evidence_id, link_data, db)
    await db.commit()
    await db.refresh(link)
    return link


@router.delete("/{case_id}/evidence/{evidence_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove an evidence link without deleting the evidence item."""
    await _get_evidence(case_id, evidence_id, db)
    await db.execute(delete(EvidenceLink).where(EvidenceLink.id == link_id, EvidenceLink.evidence_id == evidence_id))
    await db.commit()


@router.get("/{case_id}/evidence/{evidence_id}/download")
async def download_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: EvidenceStorageService = Depends(get_evidence_storage),
):
    """Download evidence through the backend."""
    evidence = await _get_evidence(case_id, evidence_id, db)
    if not evidence.storage_key:
        raise HTTPException(status_code=404, detail="Evidence has no stored file")
    stored = await storage.get_file(
        evidence.storage_key,
        evidence.file_mime_type or "application/octet-stream",
        evidence.file_name or "evidence",
    )
    return Response(
        content=stored.data,
        media_type=stored.content_type,
        headers={"Content-Disposition": f'attachment; filename="{stored.file_name}"'},
    )


@router.get("/{case_id}/evidence/{evidence_id}/thumbnail")
async def thumbnail_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: EvidenceStorageService = Depends(get_evidence_storage),
):
    """Return a sanitized evidence thumbnail through the backend."""
    evidence = await _get_evidence(case_id, evidence_id, db)
    if not evidence.thumbnail_storage_key:
        raise HTTPException(status_code=404, detail="Evidence has no thumbnail")
    stored = await storage.get_file(evidence.thumbnail_storage_key, "image/webp", "thumbnail.webp")
    return Response(content=stored.data, media_type=stored.content_type)


@router.get("/{case_id}/evidence/{evidence_id}/preview")
async def preview_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: EvidenceStorageService = Depends(get_evidence_storage),
):
    """Return a browser preview through the backend."""
    evidence = await _get_evidence(case_id, evidence_id, db)
    key = evidence.thumbnail_storage_key or evidence.storage_key
    if not key:
        raise HTTPException(status_code=404, detail="Evidence has no previewable file")
    content_type = "image/webp" if evidence.thumbnail_storage_key else evidence.file_mime_type or "application/octet-stream"
    name = "preview.webp" if evidence.thumbnail_storage_key else evidence.file_name or "evidence"
    stored = await storage.get_file(key, content_type, name)
    return Response(content=stored.data, media_type=stored.content_type)


@router.delete("/{case_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: EvidenceStorageService = Depends(get_evidence_storage),
):
    """Delete an evidence item and its stored objects."""
    evidence = await _get_evidence(case_id, evidence_id, db)
    await storage.delete_file(evidence.storage_key)
    await storage.delete_file(evidence.thumbnail_storage_key)
    await db.delete(evidence)
    await db.commit()
