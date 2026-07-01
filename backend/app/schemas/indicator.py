"""Indicator Pydantic Schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid


class IndicatorResponse(BaseModel):
    """Schema for indicator response"""
    id: uuid.UUID
    kind: str
    value: str
    label: Optional[str] = None
    meta: dict = {}
    confidence: Optional[float] = None
    first_seen: datetime
    last_verified: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
