"""Case ORM Model"""
from datetime import datetime
from typing import List
from sqlalchemy import String, Text, DateTime, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Case(Base):
    """Investigation case container"""
    __tablename__ = "cases"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    case_type: Mapped[str | None] = mapped_column(String(50))
    assigned_to: Mapped[str | None] = mapped_column(String(100))
    client: Mapped[str | None] = mapped_column(String(100))
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    
    # Target information
    target_name: Mapped[str | None] = mapped_column(String(255))
    target_aliases: Mapped[List[str] | None] = mapped_column(ARRAY(Text))
    target_location: Mapped[str | None] = mapped_column(String(255))
    target_dob: Mapped[datetime | None] = mapped_column(Date)
    
    tags: Mapped[List[str] | None] = mapped_column(ARRAY(Text))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    scans: Mapped[List["Scan"]] = relationship(
        "Scan",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    evidence: Mapped[List["Evidence"]] = relationship(
        "Evidence",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    notes: Mapped[List["CaseNote"]] = relationship(
        "CaseNote",
        back_populates="case",
        cascade="all, delete-orphan"
    )
