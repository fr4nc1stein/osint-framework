"""Scan Template ORM Model"""
from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class ScanTemplate(Base):
    """Predefined scan configurations for common use cases"""
    __tablename__ = "scan_templates"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Module configuration
    modules: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False)
    default_config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    
    # Metadata
    is_public: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[str | None] = mapped_column(String(100))
    
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
