"""Scan Template Schemas"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import uuid


class ScanTemplateCreate(BaseModel):
    """Schema for creating a scan template"""
    name: str
    description: Optional[str] = None
    category: str
    modules: List[str]
    default_config: dict = {}
    is_public: bool = True


class ScanTemplateResponse(BaseModel):
    """Schema for scan template response"""
    id: uuid.UUID
    name: str
    description: Optional[str]
    category: str
    modules: List[str]
    default_config: dict
    is_public: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
