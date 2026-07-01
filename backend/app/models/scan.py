"""Scan ORM Model"""
from datetime import datetime
from typing import List
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Scan(Base):
    """OSINT module execution job"""
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE")
    )
    parent_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL"),
        nullable=True
    )

    # Seed information
    seed_value: Mapped[str] = mapped_column(Text, nullable=False)
    seed_kind: Mapped[str] = mapped_column(String(50), nullable=False)

    # Module configuration
    modules: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total_modules: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="scans")
    findings: Mapped[List["Edge"]] = relationship(
        "Edge",
        secondary="scan_findings",
        back_populates="scans"
    )
    # Self-referential parent/child hierarchy
    parent: Mapped["Scan | None"] = relationship(
        "Scan", remote_side="Scan.id", back_populates="children", foreign_keys="Scan.parent_scan_id"
    )
    children: Mapped[List["Scan"]] = relationship(
        "Scan", back_populates="parent", foreign_keys="Scan.parent_scan_id"
    )
