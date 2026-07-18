"""Report Pydantic Schemas"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    report_format: str = Field(default="markdown", pattern="^(markdown|text|html|pdf)$")
    report_type: str = Field(default="summary", pattern="^(summary|technical|timeline|dossier|full)$")
    generated_by: str = Field(default="user")


class ReportResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    title: str
    content: Optional[str] = None
    report_format: str
    report_type: str
    generated_by: str
    generated_at: datetime
    snapshot: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}
