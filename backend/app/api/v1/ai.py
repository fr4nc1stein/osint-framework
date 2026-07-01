"""AI Settings & Analysis API"""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.case import Case
from app.models.scan import Scan

router = APIRouter()


class AnalyzeRequest(BaseModel):
    case_id: Optional[uuid.UUID] = None
    scan_id: Optional[uuid.UUID] = None
    prompt: str
    context_type: str = "case"


@router.get("/settings")
async def get_ai_settings():
    """Return current AI configuration (no keys, just metadata)"""
    provider = os.getenv("AI_PROVIDER", "anthropic")
    model = os.getenv("AI_MODEL", "claude-sonnet-4-6")

    has_key = False
    if provider == "anthropic":
        has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    elif provider == "openai":
        has_key = bool(os.getenv("OPENAI_API_KEY"))
    elif provider == "ollama":
        has_key = True  # Ollama runs locally

    return {
        "provider": provider,
        "model": model,
        "has_api_key": has_key,
        "temperature": float(os.getenv("AI_TEMPERATURE", "0.3")),
        "max_tokens": int(os.getenv("AI_MAX_TOKENS", "2048")),
    }


@router.post("/analyze")
async def analyze(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send case/scan context to configured LLM and return analysis"""
    provider = os.getenv("AI_PROVIDER", "anthropic")
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

    # Anthropic
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            model = os.getenv("AI_MODEL", "claude-sonnet-4-6")
            message = client.messages.create(
                model=model,
                max_tokens=int(os.getenv("AI_MAX_TOKENS", "2048")),
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return {"response": message.content[0].text, "provider": provider, "model": model}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    # OpenAI
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            model = os.getenv("AI_MODEL", "gpt-4o")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]
            )
            return {"response": response.choices[0].message.content, "provider": provider, "model": model}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    # Ollama (local)
    elif provider == "ollama":
        try:
            import httpx
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            model = os.getenv("AI_MODEL", "llama3")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{ollama_url}/api/generate",
                    json={"model": model, "prompt": f"{system_prompt}\n\n{user_message}", "stream": False},
                    timeout=60,
                )
                data = resp.json()
                return {"response": data.get("response", ""), "provider": provider, "model": model}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama request failed: {str(e)}")

    raise HTTPException(status_code=400, detail=f"Unsupported AI provider: {provider}")
