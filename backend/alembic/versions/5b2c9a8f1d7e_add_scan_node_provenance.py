"""add scan node provenance

Revision ID: 5b2c9a8f1d7e
Revises: e24a5fd8b0ce
Create Date: 2026-07-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5b2c9a8f1d7e"
down_revision: Union[str, None] = "e24a5fd8b0ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("launch_source", sa.String(length=30), server_default="manual", nullable=False))
    op.add_column("scans", sa.Column("source_node_type", sa.String(length=30), nullable=True))
    op.add_column("scans", sa.Column("source_node_id", sa.UUID(), nullable=True))
    op.add_column("scans", sa.Column("source_node_label", sa.Text(), nullable=True))
    op.add_column(
        "scans",
        sa.Column("source_context", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
    )
    op.create_index(
        "idx_scans_source_node",
        "scans",
        ["case_id", "source_node_type", "source_node_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_scans_source_node", table_name="scans")
    op.drop_column("scans", "source_context")
    op.drop_column("scans", "source_node_label")
    op.drop_column("scans", "source_node_id")
    op.drop_column("scans", "source_node_type")
    op.drop_column("scans", "launch_source")
