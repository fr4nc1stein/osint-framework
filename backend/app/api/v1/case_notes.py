"""Case Notes API Endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.case import Case
from app.models.case_note import CaseNote
from app.schemas.case_note import CaseNoteCreate, CaseNoteUpdate, CaseNoteResponse

router = APIRouter()


@router.post("/{case_id}/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    case_id: uuid.UUID,
    note_data: CaseNoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a note to a case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    note = CaseNote(case_id=case_id, **note_data.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
async def list_notes(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all notes for a case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    result = await db.execute(
        select(CaseNote)
        .where(CaseNote.case_id == case_id)
        .order_by(CaseNote.created_at.desc())
    )
    return result.scalars().all()


@router.put("/{case_id}/notes/{note_id}", response_model=CaseNoteResponse)
async def update_note(
    case_id: uuid.UUID,
    note_id: uuid.UUID,
    note_data: CaseNoteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a case note"""
    result = await db.execute(
        select(CaseNote).where(CaseNote.id == note_id, CaseNote.case_id == case_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")

    for field, value in note_data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)

    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{case_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    case_id: uuid.UUID,
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a case note"""
    result = await db.execute(
        select(CaseNote).where(CaseNote.id == note_id, CaseNote.case_id == case_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    await db.delete(note)
    await db.commit()
