"""CaseNote Pydantic Schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class CaseNoteCreate(BaseModel):
    content: str = Field(..., min_length=1)
    note_type: str = Field(default="text", pattern="^(text|markdown|link)$")
    author: Optional[str] = None


class CaseNoteUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)


class CaseNoteResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    content: str
    note_type: str
    author: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
