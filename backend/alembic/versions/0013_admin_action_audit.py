"""Add immutable admin action audit log table.

Revision ID: 0013_admin_action_audit
Revises: 0012_ws_connection_tickets
Create Date: 2026-02-18 01:45:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_admin_action_audit"
down_revision = "0012_ws_connection_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_action_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_admin_action_audit_action", "admin_action_audit", ["action"], unique=False)
    op.create_index("ix_admin_action_audit_created_at", "admin_action_audit", ["created_at"], unique=False)

    op.alter_column("admin_action_audit", "summary", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_admin_action_audit_created_at", table_name="admin_action_audit")
    op.drop_index("ix_admin_action_audit_action", table_name="admin_action_audit")
    op.drop_table("admin_action_audit")

