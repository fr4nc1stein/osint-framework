"""Edge (Graph Relationship) ORM Model"""
from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Index, Table, Column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


# Association table for scan findings
scan_findings = Table(
    "scan_findings",
    Base.metadata,
    Column("scan_id", UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True),
    Column("edge_id", UUID(as_uuid=True), ForeignKey("edges.id", ondelete="CASCADE"), primary_key=True),
    Column("discovered_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
)


class Edge(Base):
    """Graph edge representing relationship between indicators"""
    __tablename__ = "edges"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    src_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicators.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dst_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicators.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    source_module: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    scans: Mapped[List["Scan"]] = relationship(
        "Scan",
        secondary=scan_findings,
        back_populates="findings"
    )
    
    __table_args__ = (
        Index(
            "idx_edges_unique",
            "src_id", "dst_id", "relationship_type", "source_module",
            unique=True
        ),
    )
