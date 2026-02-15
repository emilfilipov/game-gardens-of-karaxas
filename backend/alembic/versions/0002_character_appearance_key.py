"""Add appearance_key to characters.

Revision ID: 0002_character_appearance_key
Revises: 0001_initial
Create Date: 2026-02-15 11:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_character_appearance_key"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("appearance_key", sa.String(length=64), nullable=False, server_default="human_male"),
    )
    op.execute("UPDATE characters SET appearance_key = 'human_male' WHERE appearance_key IS NULL")


def downgrade() -> None:
    op.drop_column("characters", "appearance_key")
