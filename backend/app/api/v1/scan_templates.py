"""Scan Template API Endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.scan_template import ScanTemplate
from app.schemas.scan_template import ScanTemplateCreate, ScanTemplateResponse

router = APIRouter()


@router.post("", response_model=ScanTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: ScanTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scan template"""
    
    # Check if template name already exists
    result = await db.execute(
        select(ScanTemplate).where(ScanTemplate.name == template_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template with name '{template_data.name}' already exists"
        )
    
    template = ScanTemplate(**template_data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.get("", response_model=List[ScanTemplateResponse])
async def list_templates(
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """List all scan templates"""
    
    query = select(ScanTemplate).where(ScanTemplate.is_public == True)
    
    if category:
        query = query.where(ScanTemplate.category == category)
    
    result = await db.execute(query.order_by(ScanTemplate.name))
    templates = result.scalars().all()
    
    return templates


@router.get("/{template_id}", response_model=ScanTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific scan template"""
    
    result = await db.execute(
        select(ScanTemplate).where(ScanTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a scan template"""
    
    result = await db.execute(
        select(ScanTemplate).where(ScanTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    await db.delete(template)
    await db.commit()
