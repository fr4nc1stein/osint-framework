"""Case timeline ORM models."""
from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CaseTimelineEvent(Base):
    """Chronological investigation event inside a case."""
    __tablename__ = "case_timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    occurred_at_precision: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str | None] = mapped_column(String(80))
    location_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    verification_status: Mapped[str] = mapped_column(String(30), default="lead", nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False, index=True)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship("Case", back_populates="timeline_events")
    links: Mapped[list["CaseTimelineLink"]] = relationship(
        "CaseTimelineLink",
        back_populates="timeline_event",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_case_timeline_case_time", "case_id", "occurred_at"),
        Index("idx_case_timeline_case_type", "case_id", "event_type"),
    )


class CaseTimelineLink(Base):
    """Reusable link from a timeline event to a case object."""
    __tablename__ = "case_timeline_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    timeline_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("case_timeline_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    timeline_event: Mapped["CaseTimelineEvent"] = relationship("CaseTimelineEvent", back_populates="links")

    __table_args__ = (
        Index("idx_case_timeline_links_target", "target_type", "target_id"),
    )
