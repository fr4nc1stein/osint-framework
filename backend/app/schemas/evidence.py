"""Evidence Pydantic schemas."""
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


TARGET_TYPE_PATTERN = "^(entity|relationship|timeline_event|finding|report|scan|indicator|graph_edge|note|case)$"
SOURCE_TYPE_PATTERN = "^(manual|scan|integration|import|ai_suggested)$"
EVIDENCE_TYPE_PATTERN = "^(note|url|screenshot|image|document|pdf|text|scan_result|api_response|map_location|analyst_observation)$"


class EvidenceLinkBase(BaseModel):
    target_type: str = Field(..., pattern=TARGET_TYPE_PATTERN)
    target_id: uuid.UUID
    relationship_note: Optional[str] = None


class EvidenceLinkCreate(EvidenceLinkBase):
    pass


class EvidenceLinkResponse(EvidenceLinkBase):
    id: uuid.UUID
    evidence_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    evidence_type: str = Field(default="note", pattern=EVIDENCE_TYPE_PATTERN)
    source_type: str = Field(default="manual", pattern=SOURCE_TYPE_PATTERN)
    source_url: Optional[str] = None
    captured_at: Optional[datetime] = None
    collected_by: Optional[str] = Field(default=None, max_length=100)
    chain_of_custody_status: str = Field(default="collected", max_length=30)
    metadata: dict = Field(default_factory=dict)
    link: Optional[EvidenceLinkCreate] = None


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    case_id: Optional[uuid.UUID]
    scan_id: Optional[uuid.UUID]
    title: str
    evidence_type: str
    source_type: str
    source_url: Optional[str]
    description: Optional[str]
    file_name: Optional[str]
    file_mime_type: Optional[str]
    file_size: Optional[int]
    file_sha256: Optional[str]
    storage_backend: Optional[str]
    captured_at: Optional[datetime]
    collected_at: datetime
    collected_by: Optional[str]
    chain_of_custody_status: str
    confidence: Optional[str]
    tags: Optional[list[str]]
    meta: dict
    created_at: datetime
    updated_at: datetime
    links: list[EvidenceLinkResponse] = Field(default_factory=list)
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None

    model_config = {"from_attributes": True}
