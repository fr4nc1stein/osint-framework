"""add minio evidence storage

Revision ID: f19c2d8b6a41
Revises: c7b1d9a2f4e8
Create Date: 2026-07-14 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f19c2d8b6a41"
down_revision: Union[str, None] = "c7b1d9a2f4e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("source_type", sa.String(length=30), server_default="manual", nullable=False))
    op.add_column("evidence", sa.Column("file_name", sa.String(length=255), nullable=True))
    op.add_column("evidence", sa.Column("file_mime_type", sa.String(length=120), nullable=True))
    op.add_column("evidence", sa.Column("file_size", sa.BigInteger(), nullable=True))
    op.add_column("evidence", sa.Column("file_sha256", sa.String(length=64), nullable=True))
    op.add_column("evidence", sa.Column("storage_backend", sa.String(length=30), nullable=True))
    op.add_column("evidence", sa.Column("storage_key", sa.Text(), nullable=True))
    op.add_column("evidence", sa.Column("thumbnail_storage_key", sa.Text(), nullable=True))
    op.add_column("evidence", sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("evidence", sa.Column("chain_of_custody_status", sa.String(length=30), server_default="collected", nullable=False))
    op.add_column("evidence", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index(op.f("ix_evidence_source_type"), "evidence", ["source_type"], unique=False)

    op.execute("UPDATE evidence SET file_sha256 = file_hash WHERE file_sha256 IS NULL AND file_hash IS NOT NULL")

    op.create_table(
        "evidence_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("relationship_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_links_evidence_id"), "evidence_links", ["evidence_id"], unique=False)
    op.create_index(op.f("ix_evidence_links_target_id"), "evidence_links", ["target_id"], unique=False)
    op.create_index(op.f("ix_evidence_links_target_type"), "evidence_links", ["target_type"], unique=False)
    op.create_index("idx_evidence_links_target", "evidence_links", ["target_type", "target_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_evidence_links_target", table_name="evidence_links")
    op.drop_index(op.f("ix_evidence_links_target_type"), table_name="evidence_links")
    op.drop_index(op.f("ix_evidence_links_target_id"), table_name="evidence_links")
    op.drop_index(op.f("ix_evidence_links_evidence_id"), table_name="evidence_links")
    op.drop_table("evidence_links")

    op.drop_index(op.f("ix_evidence_source_type"), table_name="evidence")
    op.drop_column("evidence", "updated_at")
    op.drop_column("evidence", "chain_of_custody_status")
    op.drop_column("evidence", "captured_at")
    op.drop_column("evidence", "thumbnail_storage_key")
    op.drop_column("evidence", "storage_key")
    op.drop_column("evidence", "storage_backend")
    op.drop_column("evidence", "file_sha256")
    op.drop_column("evidence", "file_size")
    op.drop_column("evidence", "file_mime_type")
    op.drop_column("evidence", "file_name")
    op.drop_column("evidence", "source_type")
