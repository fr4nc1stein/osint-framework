"""Integration credential schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid


class IntegrationSave(BaseModel):
    api_key: str
    enabled: bool = True


class IntegrationResponse(BaseModel):
    """Returned to UI — never exposes plaintext key."""
    id: str
    provider: str
    display_name: str
    description: str
    category: str
    enabled: bool
    has_key: bool
    masked_hint: Optional[str] = None
    source: str  # "db" | "env_fallback" | "unconfigured"
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_message: Optional[str] = None
