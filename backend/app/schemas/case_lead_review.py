"""Case lead review schemas."""
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


LEAD_STATUS_PATTERN = "^(lead|needs_review|follow_up|confirmed|rejected|stale)$"
LEAD_ACTION_PATTERN = "^(confirm|reject|follow_up|stale|promote|merge)$"
TARGET_TYPE_PATTERN = "^(entity|relationship|timeline_event|geolocation|indicator|graph_edge)$"


class CaseLeadReviewAction(BaseModel):
    action: str = Field(..., pattern=LEAD_ACTION_PATTERN)
    notes: Optional[str] = None
    reviewed_by: Optional[str] = Field(default=None, max_length=100)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    merged_entity_id: Optional[uuid.UUID] = None


class CaseLeadReviewResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    review_status: str
    notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    promoted_entity_id: Optional[uuid.UUID] = None
    merged_entity_id: Optional[uuid.UUID] = None
    meta: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseLeadItem(BaseModel):
    id: str
    target_type: str
    target_id: uuid.UUID
    lead_type: str
    label: str
    value: Optional[str] = None
    description: Optional[str] = None
    relationship: Optional[str] = None
    source_type: str
    source_ref: Optional[str] = None
    source_module: Optional[str] = None
    review_status: str
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scan_origins: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    promoted_entity_id: Optional[uuid.UUID] = None
    merged_entity_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    properties: dict = Field(default_factory=dict)


class CaseLeadQueueResponse(BaseModel):
    items: list[CaseLeadItem]
    counts: dict
