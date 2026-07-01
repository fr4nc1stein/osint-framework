"""Evidence ORM Model"""
from datetime import datetime
from typing import List
from sqlalchemy import String, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Evidence(Base):
    """Evidence tracking with chain of custody"""
    __tablename__ = "evidence"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL")
    )
    
    # Evidence details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    
    # File information
    file_path: Mapped[str | None] = mapped_column(Text)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    
    # Collection metadata
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    collected_by: Mapped[str | None] = mapped_column(String(100))
    chain_of_custody: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    confidence: Mapped[str | None] = mapped_column(String(20))
    
    tags: Mapped[List[str] | None] = mapped_column(ARRAY(Text))
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="evidence")
