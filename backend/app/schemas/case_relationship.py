"""Case relationship Pydantic schemas."""
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


NODE_TYPE_PATTERN = "^(entity|indicator)$"


class CaseRelationshipBase(BaseModel):
    from_node_type: str = Field(..., pattern=NODE_TYPE_PATTERN)
    from_node_id: uuid.UUID
    to_node_type: str = Field(..., pattern=NODE_TYPE_PATTERN)
    to_node_id: uuid.UUID
    relationship_type: str = Field(..., min_length=1, max_length=50)
    label: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    properties: dict = Field(default_factory=dict)
    source_type: str = Field(default="manual", pattern="^(manual|scan|integration|import|ai_suggested)$")
    source_ref: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: str = Field(default="lead", pattern="^(lead|needs_review|follow_up|confirmed|rejected|stale)$")
    created_by: Optional[str] = None


class CaseRelationshipCreate(CaseRelationshipBase):
    pass


class CaseRelationshipUpdate(BaseModel):
    relationship_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    label: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    properties: Optional[dict] = None
    source_ref: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: Optional[str] = Field(default=None, pattern="^(lead|needs_review|follow_up|confirmed|rejected|stale)$")


class CaseRelationshipResponse(CaseRelationshipBase):
    id: uuid.UUID
    case_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
