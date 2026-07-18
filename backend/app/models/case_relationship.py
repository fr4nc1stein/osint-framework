"""Manual case relationship ORM model."""
from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CaseRelationship(Base):
    """Manual or analyst-curated edge between case graph nodes."""
    __tablename__ = "case_relationships"

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
    from_node_type: Mapped[str] = mapped_column(String(20), nullable=False)
    from_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_node_type: Mapped[str] = mapped_column(String(20), nullable=False)
    to_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False, index=True)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    verification_status: Mapped[str] = mapped_column(String(30), default="lead", nullable=False, index=True)
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

    case: Mapped["Case"] = relationship("Case", back_populates="relationships")

    __table_args__ = (
        Index("idx_case_relationships_from", "case_id", "from_node_type", "from_node_id"),
        Index("idx_case_relationships_to", "case_id", "to_node_type", "to_node_id"),
        Index("idx_case_relationships_properties_gin", "properties", postgresql_using="gin"),
    )
