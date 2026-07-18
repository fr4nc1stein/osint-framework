"""Stats & Search API"""
import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.case import Case
from app.models.scan import Scan
from app.models.indicator import Indicator
from app.models.report import Report
from app.models.integration_credential import IntegrationCredential
from app.models.ai_setting import AISetting
from app.services.credentials import PROVIDER_ENV_MAP

router = APIRouter()


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Dashboard aggregate statistics"""
    total_cases = (await db.execute(select(func.count(Case.id)))).scalar()
    active_cases = (await db.execute(select(func.count(Case.id)).where(Case.status == "active"))).scalar()
    open_cases = (await db.execute(select(func.count(Case.id)).where(Case.status == "open"))).scalar()

    total_scans = (await db.execute(select(func.count(Scan.id)))).scalar()
    running_scans = (await db.execute(select(func.count(Scan.id)).where(Scan.status == "running"))).scalar()
    completed_scans = (await db.execute(select(func.count(Scan.id)).where(Scan.status.in_(["completed", "partial"])))).scalar()
    failed_scans = (await db.execute(select(func.count(Scan.id)).where(Scan.status.in_(["error", "failed"])))).scalar()

    total_indicators = (await db.execute(select(func.count(Indicator.id)))).scalar()
    total_reports = (await db.execute(select(func.count(Report.id)))).scalar()

    # Recent scans (last 10)
    result = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(10)
    )
    recent_scans = result.scalars().all()

    # Recent cases (last 5)
    result = await db.execute(
        select(Case).order_by(Case.created_at.desc()).limit(5)
    )
    recent_cases = result.scalars().all()

    return {
        "cases": {
            "total": total_cases,
            "active": active_cases,
            "open": open_cases,
        },
        "scans": {
            "total": total_scans,
            "running": running_scans,
            "completed": completed_scans,
            "failed": failed_scans,
        },
        "indicators": total_indicators,
        "reports": total_reports,
        "recent_scans": [
            {
                "id": str(s.id),
                "seed_value": s.seed_value,
                "seed_kind": s.seed_kind,
                "status": s.status,
                "case_id": str(s.case_id) if s.case_id else None,
                "created_at": s.created_at.isoformat(),
            }
            for s in recent_scans
        ],
        "recent_cases": [
            {
                "id": str(c.id),
                "case_number": c.case_number,
                "title": c.title,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at.isoformat(),
            }
            for c in recent_cases
        ],
    }


@router.get("/setup/status")
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    """Return first-run setup status — which providers are configured and from where."""
    # Integration credentials in DB
    result = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.encrypted_key.isnot(None))
    )
    db_creds = result.scalars().all()
    db_providers = {c.provider for c in db_creds if c.enabled}

    # Keys available in env
    env_providers = {p for p, env_var in PROVIDER_ENV_MAP.items() if os.getenv(env_var)}

    # Providers in env but not yet saved to DB
    importable = sorted(env_providers - db_providers)

    # AI setting
    ai_result = await db.execute(
        select(AISetting).where(AISetting.is_default == True)
    )
    ai_setting = ai_result.scalar_one_or_none()
    ai_configured_db = bool(ai_setting and (ai_setting.encrypted_api_key or ai_setting.provider == "ollama"))
    ai_configured_env = bool(
        os.getenv("ANTHROPIC_API_KEY") or
        os.getenv("OPENAI_API_KEY") or
        os.getenv("AI_PROVIDER") == "ollama"
    )

    needs_setup = len(db_providers) == 0 and not ai_configured_db

    return {
        "needs_setup":        needs_setup,
        "integrations_in_db": len(db_providers),
        "integrations_in_env":len(env_providers),
        "importable_count":   len(importable),
        "importable":         importable,
        "ai_configured_db":   ai_configured_db,
        "ai_configured_env":  ai_configured_env,
        "ai_source":          "db" if ai_configured_db else ("env_fallback" if ai_configured_env else "unconfigured"),
    }


search_router = APIRouter()


@search_router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db)
):
    """Search across cases, scans, and indicators"""
    pattern = f"%{q}%"

    cases_result = await db.execute(
        select(Case)
        .where(Case.title.ilike(pattern) | Case.description.ilike(pattern))
        .limit(10)
    )
    cases = cases_result.scalars().all()

    scans_result = await db.execute(
        select(Scan).where(Scan.seed_value.ilike(pattern)).limit(10)
    )
    scans = scans_result.scalars().all()

    indicators_result = await db.execute(
        select(Indicator).where(Indicator.value.ilike(pattern)).limit(10)
    )
    indicators = indicators_result.scalars().all()

    return {
        "query": q,
        "results": {
            "cases": [
                {"id": str(c.id), "title": c.title, "status": c.status, "case_number": c.case_number}
                for c in cases
            ],
            "scans": [
                {"id": str(s.id), "seed_value": s.seed_value, "seed_kind": s.seed_kind, "status": s.status}
                for s in scans
            ],
            "indicators": [
                {"id": str(i.id), "value": i.value, "kind": i.kind}
                for i in indicators
            ],
        },
    }
