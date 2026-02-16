"""Add level-builder schema and optional level assignment per character.

Revision ID: 0004_levels_tool
Revises: 0003_char_levels_unique_name
Create Date: 2026-02-16 08:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_levels_tool"
down_revision = "0003_char_levels_unique_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "levels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("spawn_x", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("spawn_y", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("wall_cells", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("uq_levels_name_ci", "levels", [sa.text("lower(name)")], unique=True)

    op.add_column(
        "characters",
        sa.Column("level_id", sa.Integer(), sa.ForeignKey("levels.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_characters_level_id", "characters", ["level_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_characters_level_id", table_name="characters")
    op.drop_column("characters", "level_id")

    op.drop_index("uq_levels_name_ci", table_name="levels")
    op.drop_table("levels")
