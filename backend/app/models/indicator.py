"""Indicator (Graph Node) ORM Model"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Indicator(Base):
    """Graph node representing discovered information"""
    __tablename__ = "indicators"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(255))
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index("idx_indicators_kind_value", "kind", "value", unique=True),
        Index("idx_indicators_meta_gin", "meta", postgresql_using="gin"),
    )
