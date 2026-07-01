"""Reports API Endpoints"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.edge import Edge, scan_findings
from app.models.indicator import Indicator
from app.models.report import Report
from app.models.scan import Scan
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter()


def _fmt_dt(value) -> str:
    return value.isoformat() if value else "n/a"


def _report_heading(report_format: str, text: str, level: int = 2) -> str:
    if report_format == "text":
        return f"\n{text}\n{'=' * len(text)}\n" if level == 1 else f"\n{text}\n{'-' * len(text)}\n"
    return f"\n{'#' * level} {text}\n"


def _bullet(report_format: str, text: str) -> str:
    return f"- {text}"


async def generate_case_report_content(
    case: Case,
    report_data: ReportCreate,
    db: AsyncSession,
) -> str:
    """Build a deterministic case report when the client does not provide content."""
    report_format = report_data.report_format

    scans_result = await db.execute(
        select(Scan)
        .where(Scan.case_id == case.id)
        .order_by(Scan.created_at)
    )
    scans = scans_result.scalars().all()

    notes_result = await db.execute(
        select(CaseNote)
        .where(CaseNote.case_id == case.id)
        .order_by(CaseNote.created_at.desc())
        .limit(10)
    )
    notes = notes_result.scalars().all()

    scan_ids = [scan.id for scan in scans]
    edges = []
    indicators = []

    if scan_ids:
        edges_result = await db.execute(
            select(Edge)
            .join(scan_findings, Edge.id == scan_findings.c.edge_id)
            .where(scan_findings.c.scan_id.in_(scan_ids))
            .order_by(Edge.created_at.desc())
            .limit(50)
        )
        edges = edges_result.scalars().all()

        indicator_ids = set()
        for edge in edges:
            indicator_ids.add(edge.src_id)
            indicator_ids.add(edge.dst_id)

        if indicator_ids:
            indicators_result = await db.execute(
                select(Indicator)
                .where(Indicator.id.in_(indicator_ids))
                .order_by(Indicator.kind, Indicator.value)
                .limit(50)
            )
            indicators = indicators_result.scalars().all()

    title = report_data.title or f"{case.title} Report"
    lines = [
        _report_heading(report_format, title, level=1).strip(),
        "",
        _bullet(report_format, f"Case: {case.title} ({case.case_number})"),
        _bullet(report_format, f"Status: {case.status}"),
        _bullet(report_format, f"Priority: {case.priority}"),
        _bullet(report_format, f"Generated at: {datetime.utcnow().isoformat()}"),
    ]

    if case.description:
        lines.extend([
            _report_heading(report_format, "Case Description").strip(),
            case.description,
        ])

    lines.extend([
        _report_heading(report_format, "Scan Summary").strip(),
        _bullet(report_format, f"Total scans: {len(scans)}"),
    ])

    if scans:
        for scan in scans:
            module_states = scan.module_statuses or {}
            completed = sum(1 for state in module_states.values() if state.get("status") == "completed")
            failed = sum(1 for state in module_states.values() if state.get("status") in {"failed", "rate_limited"})
            lines.append(_bullet(
                report_format,
                f"{scan.seed_value} ({scan.seed_kind}) - {scan.status}, "
                f"{scan.progress}/{scan.total_modules} modules complete, "
                f"{completed} succeeded, {failed} failed"
            ))
    else:
        lines.append(_bullet(report_format, "No scans have been run for this case."))

    if report_data.report_type in {"technical", "full", "summary"}:
        lines.extend([
            _report_heading(report_format, "Indicators").strip(),
        ])
        if indicators:
            for indicator in indicators[:25]:
                confidence = f", confidence {float(indicator.confidence):.2f}" if indicator.confidence is not None else ""
                lines.append(_bullet(report_format, f"{indicator.kind}: {indicator.value}{confidence}"))
        else:
            lines.append(_bullet(report_format, "No indicators found."))

        lines.extend([
            _report_heading(report_format, "Relationships").strip(),
        ])
        if edges:
            indicator_lookup = {indicator.id: indicator for indicator in indicators}
            for edge in edges[:25]:
                src = indicator_lookup.get(edge.src_id)
                dst = indicator_lookup.get(edge.dst_id)
                src_value = src.value if src else str(edge.src_id)
                dst_value = dst.value if dst else str(edge.dst_id)
                lines.append(_bullet(
                    report_format,
                    f"{src_value} {edge.relationship_type} {dst_value} "
                    f"({edge.source_module}, confidence {float(edge.confidence):.2f})"
                ))
        else:
            lines.append(_bullet(report_format, "No relationships found."))

    if report_data.report_type in {"timeline", "full"}:
        lines.extend([
            _report_heading(report_format, "Timeline").strip(),
            _bullet(report_format, f"Case created: {_fmt_dt(case.created_at)}"),
        ])
        for scan in scans:
            lines.append(_bullet(report_format, f"Scan created: {_fmt_dt(scan.created_at)} - {scan.seed_value}"))
            if scan.finished_at:
                lines.append(_bullet(report_format, f"Scan finished: {_fmt_dt(scan.finished_at)} - {scan.seed_value} ({scan.status})"))

    lines.extend([
        _report_heading(report_format, "Notes").strip(),
    ])
    if notes:
        for note in notes:
            excerpt = note.content.strip().replace("\n", " ")
            lines.append(_bullet(report_format, f"{_fmt_dt(note.created_at)}: {excerpt}"))
    else:
        lines.append(_bullet(report_format, "No case notes recorded."))

    if report_data.report_type in {"summary", "full"}:
        high_signal = [
            edge for edge in edges
            if edge.relationship_type.upper() in {"FOUND_IN_BREACH", "HAS_VULNERABILITY", "FLAGGED_AS", "HAS_REPUTATION"}
        ]
        lines.extend([
            _report_heading(report_format, "Analyst Follow-Up").strip(),
        ])
        if high_signal:
            lines.append(_bullet(report_format, f"Review {len(high_signal)} high-signal relationship(s) for validation."))
        if any(scan.status in {"partial", "failed", "error"} for scan in scans):
            lines.append(_bullet(report_format, "Review failed or partial scans and rerun missing modules where appropriate."))
        lines.append(_bullet(report_format, "Validate all findings against source evidence before external distribution."))

    return "\n".join(lines).strip() + "\n"


async def hydrate_report_content(report: Report, db: AsyncSession) -> Report:
    """Populate legacy empty reports in API responses without requiring a DB backfill."""
    if report.content:
        return report

    result = await db.execute(select(Case).where(Case.id == report.case_id))
    case = result.scalar_one_or_none()
    if not case:
        return report

    report.content = await generate_case_report_content(
        case,
        ReportCreate(
            title=report.title,
            content=report.content,
            report_format=report.report_format,
            report_type=report.report_type,
            generated_by=report.generated_by,
        ),
        db,
    )
    return report


@router.post("/{case_id}/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    case_id: uuid.UUID,
    report_data: ReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """Generate a report for a case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    report_payload = report_data.model_dump()
    if not report_payload.get("content"):
        report_payload["content"] = await generate_case_report_content(case, report_data, db)

    report = Report(case_id=case_id, **report_payload)
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
    reports = result.scalars().all()
    return [await hydrate_report_content(report, db) for report in reports]


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
    reports = result.scalars().all()
    return [await hydrate_report_content(report, db) for report in reports]


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
    return await hydrate_report_content(report, db)


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
