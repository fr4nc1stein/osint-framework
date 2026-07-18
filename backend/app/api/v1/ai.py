"""AI Settings & Analysis API"""
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.crypto import encrypt, decrypt, mask_hint
from app.models.ai_setting import AISetting
from app.models.case import Case
from app.models.scan import Scan

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class AISave(BaseModel):
    provider: str       # anthropic | openai | ollama
    model: str
    api_key: Optional[str] = None   # None = keep existing
    base_url: Optional[str] = None  # for ollama / custom endpoints
    temperature: float = 0.3
    max_tokens: int = 2048
    enabled: bool = True

class AnalyzeRequest(BaseModel):
    case_id: Optional[uuid.UUID] = None
    scan_id: Optional[uuid.UUID] = None
    prompt: str
    context_type: str = "case"

# ── Provider defaults ─────────────────────────────────────────────────────────

PROVIDER_DEFAULTS = {
    "anthropic": {"model": "claude-sonnet-4-6", "env_key": "ANTHROPIC_API_KEY"},
    "openai":    {"model": "gpt-4o",            "env_key": "OPENAI_API_KEY"},
    "ollama":    {"model": "llama3",             "env_key": None},
}

PROVIDER_MODELS = {
    "anthropic": ["claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5-20251001"],
    "openai":    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "ollama":    ["llama3", "mistral", "codellama", "gemma"],
}

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_default_setting(db: AsyncSession) -> Optional[AISetting]:
    result = await db.execute(
        select(AISetting).where(AISetting.is_default == True).where(AISetting.enabled == True)
    )
    return result.scalar_one_or_none()


async def _get_active_config(db: AsyncSession) -> dict:
    """Return active AI config — DB first, .env fallback."""
    setting = await _get_default_setting(db)

    if setting:
        api_key = None
        if setting.encrypted_api_key:
            try:
                api_key = decrypt(setting.encrypted_api_key)
            except Exception:
                api_key = None
        # For ollama, try env fallback for key (usually not needed)
        if not api_key and setting.provider != "ollama":
            env_key = PROVIDER_DEFAULTS.get(setting.provider, {}).get("env_key")
            if env_key:
                api_key = os.getenv(env_key)
        return {
            "provider":    setting.provider,
            "model":       setting.model,
            "api_key":     api_key,
            "base_url":    setting.base_url or os.getenv("OLLAMA_URL", "http://localhost:11434"),
            "temperature": setting.temperature,
            "max_tokens":  setting.max_tokens,
            "source":      "db",
        }

    # .env fallback
    provider = os.getenv("AI_PROVIDER", "anthropic")
    env_key  = PROVIDER_DEFAULTS.get(provider, {}).get("env_key")
    api_key  = os.getenv(env_key) if env_key else None
    return {
        "provider":    provider,
        "model":       os.getenv("AI_MODEL", PROVIDER_DEFAULTS.get(provider, {}).get("model", "gpt-4o")),
        "api_key":     api_key,
        "base_url":    os.getenv("OLLAMA_URL", "http://localhost:11434"),
        "temperature": float(os.getenv("AI_TEMPERATURE", "0.3")),
        "max_tokens":  int(os.getenv("AI_MAX_TOKENS", "2048")),
        "source":      "env_fallback",
    }


async def _test_provider(provider: str, model: str, api_key: Optional[str], base_url: str) -> tuple[str, str]:
    """Return ('ok'|'fail', message)."""
    try:
        if provider == "anthropic":
            if not api_key:
                return "fail", "No API key configured"
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=model, max_tokens=16,
                messages=[{"role": "user", "content": "Say: ok"}]
            )
            return "ok", f"Connected — {model}"

        elif provider == "openai":
            if not api_key:
                return "fail", "No API key configured"
            import openai
            client = openai.OpenAI(api_key=api_key)
            client.models.retrieve(model)
            return "ok", f"Connected — {model}"

        elif provider == "ollama":
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{base_url}/api/tags")
                if r.status_code == 200:
                    return "ok", f"Ollama running at {base_url}"
                return "fail", f"Ollama HTTP {r.status_code}"

        return "fail", f"Unknown provider: {provider}"
    except Exception as e:
        return "fail", str(e)[:120]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_ai_settings(db: AsyncSession = Depends(get_db)):
    """Return active AI configuration — never exposes plaintext key."""
    setting = await _get_default_setting(db)

    if setting:
        env_key_name = PROVIDER_DEFAULTS.get(setting.provider, {}).get("env_key")
        has_db_key   = bool(setting.encrypted_api_key)
        has_env_key  = bool(os.getenv(env_key_name)) if env_key_name else False
        return {
            "id":               str(setting.id),
            "provider":         setting.provider,
            "model":            setting.model,
            "base_url":         setting.base_url,
            "temperature":      setting.temperature,
            "max_tokens":       setting.max_tokens,
            "enabled":          setting.enabled,
            "has_api_key":      has_db_key or has_env_key or setting.provider == "ollama",
            "masked_hint":      setting.masked_hint,
            "source":           "db",
            "last_tested_at":   setting.last_tested_at,
            "last_test_status": setting.last_test_status,
            "last_test_message":setting.last_test_message,
        }

    # env fallback
    provider = os.getenv("AI_PROVIDER", "anthropic")
    env_key  = PROVIDER_DEFAULTS.get(provider, {}).get("env_key")
    has_key  = bool(os.getenv(env_key)) if env_key else provider == "ollama"
    return {
        "id":               None,
        "provider":         provider,
        "model":            os.getenv("AI_MODEL", PROVIDER_DEFAULTS.get(provider, {}).get("model", "")),
        "base_url":         os.getenv("OLLAMA_URL", "http://localhost:11434"),
        "temperature":      float(os.getenv("AI_TEMPERATURE", "0.3")),
        "max_tokens":       int(os.getenv("AI_MAX_TOKENS", "2048")),
        "enabled":          True,
        "has_api_key":      has_key,
        "masked_hint":      None,
        "source":           "env_fallback",
        "last_tested_at":   None,
        "last_test_status": None,
        "last_test_message":None,
    }


@router.get("/providers")
async def get_providers():
    """Return static provider catalog and model lists."""
    return [
        {"id": p, "models": PROVIDER_MODELS.get(p, []), "needs_key": p != "ollama"}
        for p in ["anthropic", "openai", "ollama"]
    ]


@router.put("/settings")
async def save_ai_settings(body: AISave, db: AsyncSession = Depends(get_db)):
    """Save or update the default AI provider settings."""
    if body.provider not in PROVIDER_DEFAULTS:
        raise HTTPException(status_code=422, detail=f"Unknown provider: {body.provider}")

    # Get existing or create new
    result = await db.execute(
        select(AISetting).where(AISetting.provider == body.provider)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        setting = AISetting(provider=body.provider)
        db.add(setting)

    setting.model       = body.model
    setting.temperature = body.temperature
    setting.max_tokens  = body.max_tokens
    setting.enabled     = body.enabled
    setting.is_default  = True
    if body.base_url is not None:
        setting.base_url = body.base_url or None

    # Encrypt new key if provided
    if body.api_key and body.api_key.strip():
        setting.encrypted_api_key = encrypt(body.api_key.strip())
        setting.masked_hint        = mask_hint(body.api_key.strip())

    # Clear is_default on other providers
    await db.execute(
        select(AISetting).where(AISetting.provider != body.provider)
    )
    other = await db.execute(
        select(AISetting).where(AISetting.provider != body.provider).where(AISetting.is_default == True)
    )
    for other_setting in other.scalars().all():
        other_setting.is_default = False

    await db.commit()
    await db.refresh(setting)

    return await get_ai_settings(db)


@router.post("/test")
async def test_ai_settings(db: AsyncSession = Depends(get_db)):
    """Test the active AI provider configuration."""
    config = await _get_active_config(db)
    status, message = await _test_provider(
        config["provider"], config["model"], config["api_key"], config["base_url"]
    )

    # Persist result if we have a DB setting
    setting = await _get_default_setting(db)
    if setting:
        setting.last_tested_at    = datetime.utcnow()
        setting.last_test_status  = status
        setting.last_test_message = message
        await db.commit()

    return {"status": status, "message": message, "provider": config["provider"]}


@router.post("/analyze")
async def analyze(request: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """Send case/scan context to configured LLM and return analysis."""
    config = await _get_active_config(db)
    provider = config["provider"]
    api_key  = config["api_key"]

    context_lines = [f"User prompt: {request.prompt}", ""]

    if request.case_id:
        result = await db.execute(select(Case).where(Case.id == request.case_id))
        case = result.scalar_one_or_none()
        if case:
            context_lines.append(f"Case: {case.title} [{case.case_number}]")
            context_lines.append(f"Status: {case.status} | Priority: {case.priority}")
            if case.description:
                context_lines.append(f"Description: {case.description}")

    if request.scan_id:
        result = await db.execute(select(Scan).where(Scan.id == request.scan_id))
        scan = result.scalar_one_or_none()
        if scan:
            context_lines.append(f"Scan target: {scan.seed_value} ({scan.seed_kind})")
            context_lines.append(f"Modules: {', '.join(scan.modules)}")
            context_lines.append(f"Status: {scan.status}")

    system_prompt = (
        "You are an OSINT analyst assistant. Analyze the provided investigation data "
        "and give concise, actionable insights. Focus on key findings, patterns, and "
        "recommended next steps."
    )
    user_message = "\n".join(context_lines)

    if provider == "anthropic":
        if not api_key:
            raise HTTPException(status_code=503, detail="Anthropic API key not configured")
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=config["model"],
                max_tokens=config["max_tokens"],
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return {"response": msg.content[0].text, "provider": provider, "model": config["model"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    elif provider == "openai":
        if not api_key:
            raise HTTPException(status_code=503, detail="OpenAI API key not configured")
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]
            )
            return {"response": resp.choices[0].message.content, "provider": provider, "model": config["model"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    elif provider == "ollama":
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{config['base_url']}/api/generate",
                    json={"model": config["model"], "prompt": f"{system_prompt}\n\n{user_message}", "stream": False},
                    timeout=60,
                )
                data = resp.json()
                return {"response": data.get("response", ""), "provider": provider, "model": config["model"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama request failed: {str(e)}")

    raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
