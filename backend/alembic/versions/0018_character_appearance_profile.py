"""Persist character appearance profile payload.

Revision ID: 0018_character_appearance_profile
Revises: 0017_level_schema_v3_objects
Create Date: 2026-02-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_character_appearance_profile"
down_revision = "0017_level_schema_v3_objects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("appearance_profile", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.alter_column("characters", "appearance_profile", server_default=None)


def downgrade() -> None:
    op.drop_column("characters", "appearance_profile")

