"""Case Pydantic Schemas"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class CaseBase(BaseModel):
    """Base case schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="open", pattern="^(open|active|closed|archived)$")
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    case_type: Optional[str] = None
    assigned_to: Optional[str] = None
    client: Optional[str] = None
    jurisdiction: Optional[str] = None
    target_name: Optional[str] = None
    target_aliases: Optional[List[str]] = None
    target_location: Optional[str] = None
    target_dob: Optional[date] = None
    tags: Optional[List[str]] = None


class CaseCreate(CaseBase):
    """Schema for creating a case"""
    case_number: Optional[str] = None


class CaseUpdate(BaseModel):
    """Schema for updating a case"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|active|closed|archived)$")
    priority: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    case_type: Optional[str] = None
    assigned_to: Optional[str] = None
    client: Optional[str] = None
    jurisdiction: Optional[str] = None
    target_name: Optional[str] = None
    target_aliases: Optional[List[str]] = None
    target_location: Optional[str] = None
    target_dob: Optional[date] = None
    tags: Optional[List[str]] = None
    closed_reason: Optional[str] = None


class CaseStatusUpdate(BaseModel):
    """Schema for changing case workflow status"""
    status: str = Field(..., pattern="^(open|active|closed|archived)$")
    closed_reason: Optional[str] = None


class CaseResponse(CaseBase):
    """Schema for case response"""
    id: uuid.UUID
    case_number: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    closed_reason: Optional[str] = None

    model_config = {"from_attributes": True}
