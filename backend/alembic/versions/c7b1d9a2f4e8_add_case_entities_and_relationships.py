"""add case entities and relationships

Revision ID: c7b1d9a2f4e8
Revises: 31fd61780482
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c7b1d9a2f4e8"
down_revision: Union[str, None] = "31fd61780482"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_entities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False),
        sa.Column("visibility", sa.String(length=30), nullable=False),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_case_entities_case_type_value", "case_entities", ["case_id", "type", "value"], unique=False)
    op.create_index("idx_case_entities_properties_gin", "case_entities", ["properties"], unique=False, postgresql_using="gin")
    op.create_index(op.f("ix_case_entities_case_id"), "case_entities", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_entities_source_type"), "case_entities", ["source_type"], unique=False)
    op.create_index(op.f("ix_case_entities_type"), "case_entities", ["type"], unique=False)
    op.create_index(op.f("ix_case_entities_verification_status"), "case_entities", ["verification_status"], unique=False)

    op.create_table(
        "case_relationships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("from_node_type", sa.String(length=20), nullable=False),
        sa.Column("from_node_id", sa.UUID(), nullable=False),
        sa.Column("to_node_type", sa.String(length=20), nullable=False),
        sa.Column("to_node_id", sa.UUID(), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_case_relationships_from", "case_relationships", ["case_id", "from_node_type", "from_node_id"], unique=False)
    op.create_index("idx_case_relationships_properties_gin", "case_relationships", ["properties"], unique=False, postgresql_using="gin")
    op.create_index("idx_case_relationships_to", "case_relationships", ["case_id", "to_node_type", "to_node_id"], unique=False)
    op.create_index(op.f("ix_case_relationships_case_id"), "case_relationships", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_relationships_relationship_type"), "case_relationships", ["relationship_type"], unique=False)
    op.create_index(op.f("ix_case_relationships_source_type"), "case_relationships", ["source_type"], unique=False)
    op.create_index(op.f("ix_case_relationships_verification_status"), "case_relationships", ["verification_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_relationships_verification_status"), table_name="case_relationships")
    op.drop_index(op.f("ix_case_relationships_source_type"), table_name="case_relationships")
    op.drop_index(op.f("ix_case_relationships_relationship_type"), table_name="case_relationships")
    op.drop_index(op.f("ix_case_relationships_case_id"), table_name="case_relationships")
    op.drop_index("idx_case_relationships_to", table_name="case_relationships")
    op.drop_index("idx_case_relationships_properties_gin", table_name="case_relationships")
    op.drop_index("idx_case_relationships_from", table_name="case_relationships")
    op.drop_table("case_relationships")

    op.drop_index(op.f("ix_case_entities_verification_status"), table_name="case_entities")
    op.drop_index(op.f("ix_case_entities_type"), table_name="case_entities")
    op.drop_index(op.f("ix_case_entities_source_type"), table_name="case_entities")
    op.drop_index(op.f("ix_case_entities_case_id"), table_name="case_entities")
    op.drop_index("idx_case_entities_properties_gin", table_name="case_entities")
    op.drop_index("idx_case_entities_case_type_value", table_name="case_entities")
    op.drop_table("case_entities")
