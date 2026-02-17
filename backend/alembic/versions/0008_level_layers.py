"""Add layered level payload storage.

Revision ID: 0008_level_layers
Revises: 0007_character_profile_fields
Create Date: 2026-02-17 18:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_level_layers"
down_revision = "0007_character_profile_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "levels",
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "levels",
        sa.Column("layer_cells", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.execute(
        """
        UPDATE levels
        SET schema_version = 2,
            layer_cells = CASE
                WHEN wall_cells IS NULL OR wall_cells::text = '[]' THEN '{}'::json
                ELSE json_build_object(
                    '1',
                    COALESCE(
                        (
                            SELECT json_agg(
                                json_build_object(
                                    'x', (cell ->> 'x')::int,
                                    'y', (cell ->> 'y')::int,
                                    'asset_key', 'wall_block'
                                )
                            )
                            FROM json_array_elements(wall_cells) cell
                        ),
                        '[]'::json
                    )
                )
            END
        """
    )


def downgrade() -> None:
    op.drop_column("levels", "layer_cells")
    op.drop_column("levels", "schema_version")
