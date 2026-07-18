"""add case lead reviews

Revision ID: e24a5fd8b0ce
Revises: d91c8b2f6a10
Create Date: 2026-07-17 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e24a5fd8b0ce"
down_revision: Union[str, None] = "d91c8b2f6a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_lead_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("review_status", sa.String(length=30), server_default="needs_review", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=100), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("promoted_entity_id", sa.UUID(), nullable=True),
        sa.Column("merged_entity_id", sa.UUID(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merged_entity_id"], ["case_entities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["promoted_entity_id"], ["case_entities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_lead_reviews_case_id"), "case_lead_reviews", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_lead_reviews_review_status"), "case_lead_reviews", ["review_status"], unique=False)
    op.create_index(op.f("ix_case_lead_reviews_target_id"), "case_lead_reviews", ["target_id"], unique=False)
    op.create_index(op.f("ix_case_lead_reviews_target_type"), "case_lead_reviews", ["target_type"], unique=False)
    op.create_index("idx_case_lead_reviews_status", "case_lead_reviews", ["case_id", "review_status"], unique=False)
    op.create_index("idx_case_lead_reviews_target", "case_lead_reviews", ["case_id", "target_type", "target_id"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_case_lead_reviews_target", table_name="case_lead_reviews")
    op.drop_index("idx_case_lead_reviews_status", table_name="case_lead_reviews")
    op.drop_index(op.f("ix_case_lead_reviews_target_type"), table_name="case_lead_reviews")
    op.drop_index(op.f("ix_case_lead_reviews_target_id"), table_name="case_lead_reviews")
    op.drop_index(op.f("ix_case_lead_reviews_review_status"), table_name="case_lead_reviews")
    op.drop_index(op.f("ix_case_lead_reviews_case_id"), table_name="case_lead_reviews")
    op.drop_table("case_lead_reviews")
