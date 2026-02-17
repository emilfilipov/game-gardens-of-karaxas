"""Add short-lived websocket connection tickets.

Revision ID: 0012_ws_connection_tickets
Revises: 0011_publish_drain_flow
Create Date: 2026-02-18 01:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_ws_connection_tickets"
down_revision = "0011_publish_drain_flow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ws_connection_tickets",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("secret_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ws_connection_tickets_user_id", "ws_connection_tickets", ["user_id"], unique=False)
    op.create_index("ix_ws_connection_tickets_session_id", "ws_connection_tickets", ["session_id"], unique=False)
    op.create_index("ix_ws_connection_tickets_expires_at", "ws_connection_tickets", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ws_connection_tickets_expires_at", table_name="ws_connection_tickets")
    op.drop_index("ix_ws_connection_tickets_session_id", table_name="ws_connection_tickets")
    op.drop_index("ix_ws_connection_tickets_user_id", table_name="ws_connection_tickets")
    op.drop_table("ws_connection_tickets")

