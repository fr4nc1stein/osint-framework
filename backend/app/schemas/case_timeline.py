"""Case timeline Pydantic schemas."""
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field, model_validator


TARGET_TYPE_PATTERN = "^(entity|relationship|evidence|scan|indicator|graph_edge|note|case)$"
SOURCE_TYPE_PATTERN = "^(manual|scan|integration|import|ai_suggested)$"
EVENT_TYPE_PATTERN = "^(sighting|address_observed|phone_observed|email_observed|account_created|profile_updated|domain_registered|breach_observed|scan_run|report_generated|note_added|contact_attempt|employment_observed|travel_or_movement|legal_event|evidence_collected|custom)$"
PRECISION_PATTERN = "^(exact|date|month|year|approximate|unknown)$"
VERIFICATION_STATUS_PATTERN = "^(lead|needs_review|follow_up|confirmed|rejected|stale)$"


class CaseTimelineLinkBase(BaseModel):
    target_type: str = Field(..., pattern=TARGET_TYPE_PATTERN)
    target_id: uuid.UUID


class CaseTimelineLinkCreate(CaseTimelineLinkBase):
    pass


class CaseTimelineLinkResponse(CaseTimelineLinkBase):
    id: uuid.UUID
    timeline_event_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseTimelineEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: str = Field(default="custom", pattern=EVENT_TYPE_PATTERN)
    occurred_at: Optional[datetime] = None
    occurred_at_precision: str = Field(default="unknown", pattern=PRECISION_PATTERN)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    timezone: Optional[str] = Field(default=None, max_length=80)
    location_entity_id: Optional[uuid.UUID] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: str = Field(default="lead", pattern=VERIFICATION_STATUS_PATTERN)
    source_type: str = Field(default="manual", pattern=SOURCE_TYPE_PATTERN)
    source_ref: Optional[str] = Field(default=None, max_length=255)
    created_by: Optional[str] = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class CaseTimelineEventCreate(CaseTimelineEventBase):
    links: list[CaseTimelineLinkCreate] = Field(default_factory=list)


class CaseTimelineEventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: Optional[str] = Field(default=None, pattern=EVENT_TYPE_PATTERN)
    occurred_at: Optional[datetime] = None
    occurred_at_precision: Optional[str] = Field(default=None, pattern=PRECISION_PATTERN)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    timezone: Optional[str] = Field(default=None, max_length=80)
    location_entity_id: Optional[uuid.UUID] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: Optional[str] = Field(default=None, pattern=VERIFICATION_STATUS_PATTERN)
    source_ref: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class CaseTimelineEventResponse(CaseTimelineEventBase):
    id: uuid.UUID
    case_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    links: list[CaseTimelineLinkResponse] = Field(default_factory=list)
    evidence_count: int = 0

    model_config = {"from_attributes": True}
