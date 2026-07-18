"""Case geolocation schemas."""
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


TARGET_TYPE_PATTERN = "^(entity|evidence|timeline_event|graph_edge|scan|indicator|case)$"
PRECISION_PATTERN = "^(exact|building|street|city|region|country|ip_geo_approximate|unknown)$"
SOURCE_TYPE_PATTERN = "^(manual|scan|integration|import|ai_suggested|evidence)$"
STATUS_PATTERN = "^(lead|needs_review|confirmed|rejected|stale|collected)$"


class CaseGeolocationBase(BaseModel):
    target_type: str = Field(..., pattern=TARGET_TYPE_PATTERN)
    target_id: uuid.UUID
    label: Optional[str] = Field(default=None, max_length=255)
    address_text: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    precision: str = Field(default="unknown", pattern=PRECISION_PATTERN)
    geocoding_source: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: str = Field(default="lead", pattern=STATUS_PATTERN)
    source_type: str = Field(default="manual", pattern=SOURCE_TYPE_PATTERN)
    source_ref: Optional[str] = Field(default=None, max_length=255)
    evidence_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    is_primary: bool = True
    created_by: Optional[str] = Field(default=None, max_length=100)
    meta: dict = Field(default_factory=dict)


class CaseGeolocationCreate(CaseGeolocationBase):
    pass


class CaseGeolocationUpdate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=255)
    address_text: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    precision: Optional[str] = Field(default=None, pattern=PRECISION_PATTERN)
    geocoding_source: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_status: Optional[str] = Field(default=None, pattern=STATUS_PATTERN)
    source_type: Optional[str] = Field(default=None, pattern=SOURCE_TYPE_PATTERN)
    source_ref: Optional[str] = Field(default=None, max_length=255)
    evidence_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    is_primary: Optional[bool] = None
    meta: Optional[dict] = None


class CaseGeolocationResponse(CaseGeolocationBase):
    id: uuid.UUID
    case_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeocodeRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    provider: str = Field(default="mapbox", pattern="^(mapbox)$")
    limit: int = Field(default=5, ge=1, le=10)
    consent_to_external_lookup: bool = False


class GeocodeResult(BaseModel):
    provider: str
    label: str
    address_text: str
    latitude: float
    longitude: float
    precision: str
    confidence: Optional[float] = None
    source_ref: Optional[str] = None
