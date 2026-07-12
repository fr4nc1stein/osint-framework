"""AI provider settings model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AISetting(Base):
    __tablename__ = "ai_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # anthropic|openai|ollama
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    encrypted_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    masked_hint: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_status: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    last_test_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
