"""Reports API Endpoints"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
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
from app.services.report_renderer import (
    build_snapshot,
    render_html,
    render_pdf,
    render_markdown_to_html,
)

router = APIRouter()


def _fmt_dt(value) -> str:
    return value.isoformat() if value else "n/a"


def _report_heading(report_format: str, text: str, level: int = 2) -> str:
    if report_format == "text":
        return f"\n{text}\n{'=' * len(text)}\n" if level == 1 else f"\n{text}\n{'-' * len(text)}\n"
    return f"\n{'#' * level} {text}\n"


def _bullet(report_format: str, text: str) -> str:
    return f"- {text}"


async def _load_case_data(case: Case, db: AsyncSession):
    scans_result = await db.execute(
        select(Scan).where(Scan.case_id == case.id).order_by(Scan.created_at)
    )
    scans = scans_result.scalars().all()

    notes_result = await db.execute(
        select(CaseNote).where(CaseNote.case_id == case.id).order_by(CaseNote.created_at.desc()).limit(10)
    )
    notes = notes_result.scalars().all()

    scan_ids = [s.id for s in scans]
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

        ind_ids = set()
        for e in edges:
            ind_ids.add(e.src_id)
            ind_ids.add(e.dst_id)

        if ind_ids:
            inds_result = await db.execute(
                select(Indicator)
                .where(Indicator.id.in_(ind_ids))
                .order_by(Indicator.kind, Indicator.value)
                .limit(50)
            )
            indicators = inds_result.scalars().all()

    return scans, indicators, edges, notes


async def generate_markdown_content(case: Case, report_data: ReportCreate, db: AsyncSession) -> str:
    report_format = report_data.report_format
    scans, indicators, edges, notes = await _load_case_data(case, db)

    title = report_data.title or f"{case.title} Report"
    lines = [
        _report_heading(report_format, title, level=1).strip(), "",
        _bullet(report_format, f"Case: {case.title} ({case.case_number})"),
        _bullet(report_format, f"Status: {case.status}"),
        _bullet(report_format, f"Priority: {case.priority}"),
        _bullet(report_format, f"Generated at: {datetime.utcnow().isoformat()}"),
    ]

    if case.description:
        lines.extend([_report_heading(report_format, "Case Description").strip(), case.description])

    lines.extend([
        _report_heading(report_format, "Scan Summary").strip(),
        _bullet(report_format, f"Total scans: {len(scans)}"),
    ])
    for scan in scans:
        module_states = scan.module_statuses or {}
        completed = sum(1 for s in module_states.values() if s.get("status") == "completed")
        failed = sum(1 for s in module_states.values() if s.get("status") in {"failed", "rate_limited"})
        lines.append(_bullet(
            report_format,
            f"{scan.seed_value} ({scan.seed_kind}) - {scan.status}, "
            f"{scan.progress}/{scan.total_modules} modules, {completed} ok, {failed} failed"
        ))

    if report_data.report_type in {"technical", "full", "summary"}:
        lines.append(_report_heading(report_format, "Indicators").strip())
        for ind in (indicators or [])[:25]:
            conf = f", conf {float(ind.confidence):.2f}" if ind.confidence is not None else ""
            lines.append(_bullet(report_format, f"{ind.kind}: {ind.value}{conf}"))
        if not indicators:
            lines.append(_bullet(report_format, "No indicators found."))

        lines.append(_report_heading(report_format, "Relationships").strip())
        ind_lookup = {i.id: i for i in indicators}
        for edge in (edges or [])[:25]:
            src = ind_lookup.get(edge.src_id)
            dst = ind_lookup.get(edge.dst_id)
            lines.append(_bullet(
                report_format,
                f"{src.value if src else edge.src_id} {edge.relationship_type} "
                f"{dst.value if dst else edge.dst_id} ({edge.source_module}, conf {float(edge.confidence):.2f})"
            ))
        if not edges:
            lines.append(_bullet(report_format, "No relationships found."))

    if report_data.report_type in {"timeline", "full"}:
        lines.append(_report_heading(report_format, "Timeline").strip())
        lines.append(_bullet(report_format, f"Case created: {_fmt_dt(case.created_at)}"))
        for scan in scans:
            lines.append(_bullet(report_format, f"Scan: {_fmt_dt(scan.created_at)} - {scan.seed_value}"))
            if scan.finished_at:
                lines.append(_bullet(report_format, f"Done: {_fmt_dt(scan.finished_at)} - {scan.seed_value} ({scan.status})"))

    lines.append(_report_heading(report_format, "Notes").strip())
    for note in (notes or []):
        excerpt = note.content.strip().replace("\n", " ")
        lines.append(_bullet(report_format, f"{_fmt_dt(note.created_at)}: {excerpt}"))
    if not notes:
        lines.append(_bullet(report_format, "No case notes recorded."))

    if report_data.report_type in {"summary", "full"}:
        high_signal = [e for e in edges if e.relationship_type.upper() in
                       {"FOUND_IN_BREACH", "HAS_VULNERABILITY", "FLAGGED_AS", "HAS_REPUTATION"}]
        lines.append(_report_heading(report_format, "Analyst Follow-Up").strip())
        if high_signal:
            lines.append(_bullet(report_format, f"Review {len(high_signal)} high-signal relationship(s)."))
        if any(s.status in {"partial", "failed", "error"} for s in scans):
            lines.append(_bullet(report_format, "Review failed/partial scans and rerun where appropriate."))
        lines.append(_bullet(report_format, "Validate all findings before external distribution."))

    return "\n".join(lines).strip() + "\n"


async def hydrate_report_content(report: Report, db: AsyncSession) -> Report:
    if report.content:
        return report
    result = await db.execute(select(Case).where(Case.id == report.case_id))
    case = result.scalar_one_or_none()
    if not case:
        return report
    safe_fmt = "markdown" if report.report_format in {"html", "pdf"} else report.report_format
    report.content = await generate_markdown_content(
        case,
        ReportCreate(title=report.title, report_format=safe_fmt, report_type=report.report_type),
        db,
    )
    return report


def _safe_filename(title: str, ext: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)
    return f"{safe.strip().replace(' ', '_')}.{ext}"


# ---------------------------------------------------------------------------
# Case-scoped routes
# ---------------------------------------------------------------------------

@router.post("/{case_id}/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(case_id: uuid.UUID, report_data: ReportCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    scans, indicators, edges, notes = await _load_case_data(case, db)
    snapshot = build_snapshot(case, scans, indicators, edges, notes)

    safe_fmt = "markdown" if report_data.report_format in {"html", "pdf"} else report_data.report_format
    content = await generate_markdown_content(
        case,
        ReportCreate(title=report_data.title, report_format=safe_fmt, report_type=report_data.report_type),
        db,
    )

    payload = report_data.model_dump()
    payload["content"] = content
    payload["snapshot"] = snapshot

    report = Report(case_id=case_id, **payload)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{case_id}/reports", response_model=List[ReportResponse])
async def list_case_reports(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    result = await db.execute(
        select(Report).where(Report.case_id == case_id).order_by(Report.generated_at.desc())
    )
    return [await hydrate_report_content(r, db) for r in result.scalars().all()]


# ---------------------------------------------------------------------------
# Standalone report routes
# ---------------------------------------------------------------------------

router_reports_standalone = APIRouter()


@router_reports_standalone.get("", response_model=List[ReportResponse])
async def list_all_reports(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).order_by(Report.generated_at.desc()).offset(skip).limit(limit)
    )
    return [await hydrate_report_content(r, db) for r in result.scalars().all()]


@router_reports_standalone.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return await hydrate_report_content(report, db)


@router_reports_standalone.get("/{report_id}/preview")
async def preview_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Render report as HTML in the browser."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    report = await hydrate_report_content(report, db)

    if report.snapshot and report.report_format in {"html", "pdf"}:
        html = render_html(report.snapshot, report.title, report.report_type)
    else:
        html = render_markdown_to_html(report.content or "", report.title)
    return Response(content=html, media_type="text/html")


@router_reports_standalone.get("/{report_id}/download")
async def download_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Download the report in its stored format."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    report = await hydrate_report_content(report, db)
    fmt = report.report_format

    if fmt == "pdf":
        try:
            pdf_bytes = render_pdf(report.snapshot or {}, report.title, report.report_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{_safe_filename(report.title, "pdf")}"'},
        )

    if fmt == "html":
        if report.snapshot:
            html = render_html(report.snapshot, report.title, report.report_type)
        else:
            html = render_markdown_to_html(report.content or "", report.title)
        return Response(
            content=html.encode("utf-8"),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{_safe_filename(report.title, "html")}"'},
        )

    if fmt == "text":
        return Response(
            content=(report.content or "").encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{_safe_filename(report.title, "txt")}"'},
        )

    return Response(
        content=(report.content or "").encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(report.title, "md")}"'},
    )


@router_reports_standalone.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    await db.delete(report)
    await db.commit()
