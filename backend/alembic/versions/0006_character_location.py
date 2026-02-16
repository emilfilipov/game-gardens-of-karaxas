"""Persist character world location coordinates.

Revision ID: 0006_character_location
Revises: 0005_user_admin_flag
Create Date: 2026-02-16 11:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_character_location"
down_revision = "0005_user_admin_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("location_x", sa.Integer(), nullable=True))
    op.add_column("characters", sa.Column("location_y", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("characters", "location_y")
    op.drop_column("characters", "location_x")
