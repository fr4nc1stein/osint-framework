"""Scan Pydantic Schemas"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class ScanCreate(BaseModel):
    """Schema for creating a scan"""
    case_id: Optional[uuid.UUID] = None
    parent_scan_id: Optional[uuid.UUID] = None
    seed_value: str = Field(..., min_length=1)
    seed_kind: str = Field(..., pattern="^(domain|ip|email|phone|username|bitcoin)$")
    modules: List[str] = Field(..., min_items=1)


class ScanResponse(BaseModel):
    """Schema for scan response"""
    id: uuid.UUID
    case_id: Optional[uuid.UUID] = None
    parent_scan_id: Optional[uuid.UUID] = None
    seed_value: str
    seed_kind: str
    modules: List[str]
    status: str
    progress: int
    total_modules: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
