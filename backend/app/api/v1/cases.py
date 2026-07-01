"""Case Management API Endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse

router = APIRouter()


def generate_case_number() -> str:
    """Generate unique case number"""
    return f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new case"""
    case_number = case_data.case_number or generate_case_number()
    
    case = Case(
        case_number=case_number,
        **case_data.model_dump(exclude={"case_number"})
    )
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    return case


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all cases"""
    result = await db.execute(
        select(Case)
        .order_by(Case.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    cases = result.scalars().all()
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get case by ID"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )
    
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    case_data: CaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )
    
    update_data = case_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    await db.commit()
    await db.refresh(case)
    
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )
    
    await db.delete(case)
    await db.commit()
