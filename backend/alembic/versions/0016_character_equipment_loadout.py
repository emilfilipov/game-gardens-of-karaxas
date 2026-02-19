"""Persist character equipment loadout JSON.

Revision ID: 0016_character_equipment_loadout
Revises: 0015_levels_tower_order
Create Date: 2026-02-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_character_equipment_loadout"
down_revision = "0015_levels_tower_order"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("equipment", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.alter_column("characters", "equipment", server_default=None)


def downgrade() -> None:
    op.drop_column("characters", "equipment")
