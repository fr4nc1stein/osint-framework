"""Case entity Pydantic schemas."""
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


NODE_TYPE_PATTERN = "^(entity|indicator)$"


class CaseEntityBase(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1)
    description: Optional[str] = None
    properties: dict = Field(default_factory=dict)
    source_type: str = Field(default="manual", pattern="^(manual|scan|integration|import|ai_suggested)$")
    source_ref: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: str = Field(default="lead", pattern="^(lead|needs_review|confirmed|rejected|stale)$")
    visibility: str = Field(default="case", pattern="^(case|private|reportable)$")
    created_by: Optional[str] = None


class CaseEntityCreate(CaseEntityBase):
    connected_to_node_type: Optional[str] = Field(default=None, pattern=NODE_TYPE_PATTERN)
    connected_to_node_id: Optional[uuid.UUID] = None
    relationship_type: Optional[str] = Field(default=None, max_length=50)
    relationship_label: Optional[str] = Field(default=None, max_length=255)


class CaseEntityUpdate(BaseModel):
    type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    label: Optional[str] = Field(default=None, min_length=1, max_length=255)
    value: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    properties: Optional[dict] = None
    source_ref: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: Optional[str] = Field(default=None, pattern="^(lead|needs_review|confirmed|rejected|stale)$")
    visibility: Optional[str] = Field(default=None, pattern="^(case|private|reportable)$")


class CaseEntityResponse(CaseEntityBase):
    id: uuid.UUID
    case_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
