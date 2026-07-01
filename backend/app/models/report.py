"""Report ORM Model"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Report(Base):
    """Investigation report generated from a case"""
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    # "report_format" and "report_type" — avoids Python builtins "format"/"type"
    report_format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), default="summary", nullable=False)
    generated_by: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="reports")
