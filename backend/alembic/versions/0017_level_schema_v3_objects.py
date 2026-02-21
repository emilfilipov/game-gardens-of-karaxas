"""Add level object placements for schema v3 hybrid authoring.

Revision ID: 0017_level_schema_v3_objects
Revises: 0016_character_equipment_loadout
Create Date: 2026-02-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_level_schema_v3_objects"
down_revision = "0016_character_equipment_loadout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "levels",
        sa.Column("object_placements", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.alter_column("levels", "object_placements", server_default=None)


def downgrade() -> None:
    op.drop_column("levels", "object_placements")
