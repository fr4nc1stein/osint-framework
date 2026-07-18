"""Normalized case geolocation observations."""
from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CaseGeolocation(Base):
    """Location observation linked to a case object with provenance."""
    __tablename__ = "case_geolocations"

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
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(255))
    address_text: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    precision: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False, index=True)
    geocoding_source: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    verification_status: Mapped[str] = mapped_column(String(30), default="lead", nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False, index=True)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(100))
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
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

    case: Mapped["Case"] = relationship("Case", back_populates="geolocations")

    __table_args__ = (
        Index("idx_case_geolocations_target", "target_type", "target_id"),
        Index("idx_case_geolocations_case_target_primary", "case_id", "target_type", "target_id", "is_primary"),
        Index("idx_case_geolocations_meta_gin", "meta", postgresql_using="gin"),
    )
