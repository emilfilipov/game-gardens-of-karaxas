"""Add character levels/experience and global unique character names.

Revision ID: 0003_char_levels_unique_name
Revises: 0002_character_appearance_key
Create Date: 2026-02-15 17:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_char_levels_unique_name"
down_revision = "0002_character_appearance_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("level", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("characters", sa.Column("experience", sa.Integer(), nullable=False, server_default="0"))
    op.execute(
        """
        WITH duplicates AS (
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY lower(name) ORDER BY id) AS rn
                FROM characters
            ) ranked
            WHERE rn > 1
        )
        UPDATE characters c
        SET name = LEFT(c.name, GREATEST(1, 63 - LENGTH(c.id::text))) || '_' || c.id::text
        FROM duplicates d
        WHERE c.id = d.id
        """
    )
    op.create_index("uq_characters_name_ci", "characters", [sa.text("lower(name)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_characters_name_ci", table_name="characters")
    op.drop_column("characters", "experience")
    op.drop_column("characters", "level")
