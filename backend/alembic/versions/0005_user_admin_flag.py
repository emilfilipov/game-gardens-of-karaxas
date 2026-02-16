"""Add users.is_admin flag and bootstrap default admin account.

Revision ID: 0005_user_admin_flag
Revises: 0004_levels_tool
Create Date: 2026-02-16 10:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_user_admin_flag"
down_revision = "0004_levels_tool"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        """
        UPDATE users
        SET is_admin = TRUE
        WHERE lower(email) = 'admin@admin.com'
        """
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
