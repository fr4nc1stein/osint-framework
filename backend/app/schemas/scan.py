"""Scan Pydantic Schemas"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class ScanCreate(BaseModel):
    """Schema for creating a scan"""
    case_id: Optional[uuid.UUID] = None
    parent_scan_id: Optional[uuid.UUID] = None
    seed_value: str = Field(..., min_length=1)
    seed_kind: str = Field(..., pattern="^(domain|ip|email|url|phone|username|bitcoin)$")
    modules: List[str] = Field(..., min_items=1)
    launch_source: str = Field(default="manual", pattern="^(manual|case_node|api|scheduled|integration|ai_suggested)$")
    source_node_type: Optional[str] = Field(default=None, pattern="^(entity|indicator|graph_edge)$")
    source_node_id: Optional[uuid.UUID] = None
    source_node_label: Optional[str] = None
    source_context: Dict[str, Any] = Field(default_factory=dict)


class ScanResponse(BaseModel):
    """Schema for scan response"""
    id: uuid.UUID
    case_id: Optional[uuid.UUID] = None
    parent_scan_id: Optional[uuid.UUID] = None
    seed_value: str
    seed_kind: str
    launch_source: str
    source_node_type: Optional[str] = None
    source_node_id: Optional[uuid.UUID] = None
    source_node_label: Optional[str] = None
    source_context: Dict[str, Any] = Field(default_factory=dict)
    modules: List[str]
    status: str
    progress: int
    total_modules: int
    error_message: Optional[str] = None
    module_statuses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
