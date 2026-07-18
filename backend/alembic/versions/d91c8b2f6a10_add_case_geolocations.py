"""add case geolocations

Revision ID: d91c8b2f6a10
Revises: a3d8e4f9c2b7
Create Date: 2026-07-17 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d91c8b2f6a10"
down_revision: Union[str, None] = "a3d8e4f9c2b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_geolocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("address_text", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("precision", sa.String(length=30), server_default="unknown", nullable=False),
        sa.Column("geocoding_source", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("verification_status", sa.String(length=30), server_default="lead", nullable=False),
        sa.Column("source_type", sa.String(length=30), server_default="manual", nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("evidence_id", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_geolocations_case_id"), "case_geolocations", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_geolocations_precision"), "case_geolocations", ["precision"], unique=False)
    op.create_index(op.f("ix_case_geolocations_source_type"), "case_geolocations", ["source_type"], unique=False)
    op.create_index(op.f("ix_case_geolocations_target_id"), "case_geolocations", ["target_id"], unique=False)
    op.create_index(op.f("ix_case_geolocations_target_type"), "case_geolocations", ["target_type"], unique=False)
    op.create_index(op.f("ix_case_geolocations_verification_status"), "case_geolocations", ["verification_status"], unique=False)
    op.create_index("idx_case_geolocations_case_target_primary", "case_geolocations", ["case_id", "target_type", "target_id", "is_primary"], unique=False)
    op.create_index("idx_case_geolocations_meta_gin", "case_geolocations", ["meta"], unique=False, postgresql_using="gin")
    op.create_index("idx_case_geolocations_target", "case_geolocations", ["target_type", "target_id"], unique=False)

    op.execute(
        """
        INSERT INTO case_geolocations (
            id,
            case_id,
            target_type,
            target_id,
            label,
            address_text,
            latitude,
            longitude,
            precision,
            geocoding_source,
            confidence,
            verification_status,
            source_type,
            source_ref,
            notes,
            is_primary,
            created_by,
            meta,
            created_at,
            updated_at
        )
        SELECT
            (md5(random()::text || clock_timestamp()::text))::uuid,
            case_id,
            'entity',
            id,
            COALESCE(properties->>'map_label', label, value),
            COALESCE(properties->>'address_text', properties->>'address', value),
            (properties->>'latitude')::numeric,
            (properties->>'longitude')::numeric,
            COALESCE(properties->>'location_precision', properties->>'precision', 'unknown'),
            properties->>'geocoding_source',
            confidence,
            verification_status,
            source_type,
            source_ref,
            properties->>'location_note',
            true,
            created_by,
            '{"legacy_entity_properties": true}'::jsonb,
            created_at,
            updated_at
        FROM case_entities
        WHERE type IN ('address', 'location', 'office', 'company', 'organization', 'person', 'vehicle')
          AND properties ? 'latitude'
          AND properties ? 'longitude'
          AND (properties->>'latitude') ~ '^-?[0-9]+(\\.[0-9]+)?$'
          AND (properties->>'longitude') ~ '^-?[0-9]+(\\.[0-9]+)?$'
          AND (properties->>'latitude')::numeric BETWEEN -90 AND 90
          AND (properties->>'longitude')::numeric BETWEEN -180 AND 180
        """
    )


def downgrade() -> None:
    op.drop_index("idx_case_geolocations_target", table_name="case_geolocations")
    op.drop_index("idx_case_geolocations_meta_gin", table_name="case_geolocations")
    op.drop_index("idx_case_geolocations_case_target_primary", table_name="case_geolocations")
    op.drop_index(op.f("ix_case_geolocations_verification_status"), table_name="case_geolocations")
    op.drop_index(op.f("ix_case_geolocations_target_type"), table_name="case_geolocations")
    op.drop_index(op.f("ix_case_geolocations_target_id"), table_name="case_geolocations")
    op.drop_index(op.f("ix_case_geolocations_source_type"), table_name="case_geolocations")
    op.drop_index(op.f("ix_case_geolocations_precision"), table_name="case_geolocations")
    op.drop_index(op.f("ix_case_geolocations_case_id"), table_name="case_geolocations")
    op.drop_table("case_geolocations")
