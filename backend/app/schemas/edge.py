"""Edge Pydantic Schemas"""
from datetime import datetime
from pydantic import BaseModel
import uuid


class EdgeResponse(BaseModel):
    """Schema for edge response"""
    id: uuid.UUID
    src_id: uuid.UUID
    dst_id: uuid.UUID
    relationship_type: str
    confidence: float
    source_module: str
    evidence: dict = {}
    created_at: datetime
    
    model_config = {"from_attributes": True}
