"""add case timeline events

Revision ID: a3d8e4f9c2b7
Revises: f19c2d8b6a41
Create Date: 2026-07-14 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3d8e4f9c2b7"
down_revision: Union[str, None] = "f19c2d8b6a41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_timeline_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("occurred_at_precision", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=True),
        sa.Column("location_entity_id", sa.UUID(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("verification_status", sa.String(length=30), server_default="lead", nullable=False),
        sa.Column("source_type", sa.String(length=30), server_default="manual", nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_timeline_events_case_id"), "case_timeline_events", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_timeline_events_event_type"), "case_timeline_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_case_timeline_events_occurred_at"), "case_timeline_events", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_case_timeline_events_source_type"), "case_timeline_events", ["source_type"], unique=False)
    op.create_index(op.f("ix_case_timeline_events_verification_status"), "case_timeline_events", ["verification_status"], unique=False)
    op.create_index("idx_case_timeline_case_time", "case_timeline_events", ["case_id", "occurred_at"], unique=False)
    op.create_index("idx_case_timeline_case_type", "case_timeline_events", ["case_id", "event_type"], unique=False)

    op.create_table(
        "case_timeline_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("timeline_event_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["timeline_event_id"], ["case_timeline_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_timeline_links_target_id"), "case_timeline_links", ["target_id"], unique=False)
    op.create_index(op.f("ix_case_timeline_links_target_type"), "case_timeline_links", ["target_type"], unique=False)
    op.create_index(op.f("ix_case_timeline_links_timeline_event_id"), "case_timeline_links", ["timeline_event_id"], unique=False)
    op.create_index("idx_case_timeline_links_target", "case_timeline_links", ["target_type", "target_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_case_timeline_links_target", table_name="case_timeline_links")
    op.drop_index(op.f("ix_case_timeline_links_timeline_event_id"), table_name="case_timeline_links")
    op.drop_index(op.f("ix_case_timeline_links_target_type"), table_name="case_timeline_links")
    op.drop_index(op.f("ix_case_timeline_links_target_id"), table_name="case_timeline_links")
    op.drop_table("case_timeline_links")

    op.drop_index("idx_case_timeline_case_type", table_name="case_timeline_events")
    op.drop_index("idx_case_timeline_case_time", table_name="case_timeline_events")
    op.drop_index(op.f("ix_case_timeline_events_verification_status"), table_name="case_timeline_events")
    op.drop_index(op.f("ix_case_timeline_events_source_type"), table_name="case_timeline_events")
    op.drop_index(op.f("ix_case_timeline_events_occurred_at"), table_name="case_timeline_events")
    op.drop_index(op.f("ix_case_timeline_events_event_type"), table_name="case_timeline_events")
    op.drop_index(op.f("ix_case_timeline_events_case_id"), table_name="case_timeline_events")
    op.drop_table("case_timeline_events")
