"""Add level descriptive names, tower ordering, and transition links.

Revision ID: 0015_levels_tower_order_and_transitions
Revises: 0014_auth_security_hardening
Create Date: 2026-02-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_levels_tower_order_and_transitions"
down_revision = "0014_auth_security_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("levels", sa.Column("descriptive_name", sa.String(length=96), nullable=True))
    op.add_column(
        "levels",
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "levels",
        sa.Column("transitions", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )

    op.execute("UPDATE levels SET descriptive_name = name WHERE descriptive_name IS NULL OR descriptive_name = ''")
    op.execute(
        """
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY name ASC, id ASC) AS rn
            FROM levels
        )
        UPDATE levels
        SET order_index = ranked.rn
        FROM ranked
        WHERE levels.id = ranked.id
        """
    )

    op.alter_column("levels", "descriptive_name", nullable=False)
    op.create_index("ix_levels_order_index", "levels", ["order_index"], unique=False)

    op.alter_column("levels", "order_index", server_default=None)
    op.alter_column("levels", "transitions", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_levels_order_index", table_name="levels")
    op.drop_column("levels", "transitions")
    op.drop_column("levels", "order_index")
    op.drop_column("levels", "descriptive_name")
