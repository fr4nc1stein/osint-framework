"""Reports API Endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.case import Case
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter()


@router.post("/{case_id}/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    case_id: uuid.UUID,
    report_data: ReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """Generate a report for a case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    report = Report(case_id=case_id, **report_data.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{case_id}/reports", response_model=List[ReportResponse])
async def list_case_reports(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all reports for a case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    result = await db.execute(
        select(Report)
        .where(Report.case_id == case_id)
        .order_by(Report.generated_at.desc())
    )
    return result.scalars().all()


router_reports_standalone = APIRouter()


@router_reports_standalone.get("", response_model=List[ReportResponse])
async def list_all_reports(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all reports across all cases"""
    result = await db.execute(
        select(Report)
        .order_by(Report.generated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router_reports_standalone.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single report"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


@router_reports_standalone.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a report"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    await db.delete(report)
    await db.commit()
