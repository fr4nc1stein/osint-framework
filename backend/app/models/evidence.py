"""Evidence ORM models."""
from datetime import datetime
from typing import List
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Evidence(Base):
    """Evidence tracking with chain of custody."""
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
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    
    # File information
    file_path: Mapped[str | None] = mapped_column(Text)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_mime_type: Mapped[str | None] = mapped_column(String(120))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    file_sha256: Mapped[str | None] = mapped_column(String(64))
    storage_backend: Mapped[str | None] = mapped_column(String(30))
    storage_key: Mapped[str | None] = mapped_column(Text)
    thumbnail_storage_key: Mapped[str | None] = mapped_column(Text)
    
    # Collection metadata
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_by: Mapped[str | None] = mapped_column(String(100))
    chain_of_custody_status: Mapped[str] = mapped_column(String(30), default="collected", nullable=False)
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="evidence")
    links: Mapped[List["EvidenceLink"]] = relationship(
        "EvidenceLink",
        back_populates="evidence",
        cascade="all, delete-orphan",
    )


class EvidenceLink(Base):
    """Reusable link from evidence to a case object."""
    __tablename__ = "evidence_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    relationship_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    evidence: Mapped["Evidence"] = relationship("Evidence", back_populates="links")

    __table_args__ = (
        Index("idx_evidence_links_target", "target_type", "target_id"),
    )
