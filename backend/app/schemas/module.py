"""Module Pydantic Schemas"""
from typing import List
from pydantic import BaseModel, Field


class ModuleInfo(BaseModel):
    """Module metadata schema"""
    module_id: str
    display_name: str
    description: str
    category: str
    accepts: List[str]
    requires_api_key: bool = False
    api_key_configured: bool = False


class DiscoveryResult(BaseModel):
    """Discovery result from module execution"""
    src_value: str
    src_kind: str
    dst_value: str
    dst_kind: str
    relationship: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: dict = {}
    source_module: str
