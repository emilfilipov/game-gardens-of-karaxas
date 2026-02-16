"""Persist character race/background/affiliation profile fields.

Revision ID: 0007_character_profile_fields
Revises: 0006_character_location
Create Date: 2026-02-16 13:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_character_profile_fields"
down_revision = "0006_character_location"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("race", sa.String(length=64), nullable=False, server_default="Human"),
    )
    op.add_column(
        "characters",
        sa.Column("background", sa.String(length=64), nullable=False, server_default="Drifter"),
    )
    op.add_column(
        "characters",
        sa.Column("affiliation", sa.String(length=64), nullable=False, server_default="Unaffiliated"),
    )


def downgrade() -> None:
    op.drop_column("characters", "affiliation")
    op.drop_column("characters", "background")
    op.drop_column("characters", "race")
