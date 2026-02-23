"""Add gameplay authority audit table and character inventory.

Revision ID: 0020_gameplay_authority
Revises: 0019_party_instance_runtime
Create Date: 2026-02-23 00:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_gameplay_authority"
down_revision = "0019_party_instance_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("inventory", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.alter_column("characters", "inventory", server_default=None)

    op.create_table(
        "gameplay_action_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_nonce", sa.String(length=96), nullable=False),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reason_code", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "action_nonce", name="uq_gameplay_action_session_nonce"),
    )
    op.create_index("ix_gameplay_action_audit_session_id", "gameplay_action_audit", ["session_id"])
    op.create_index("ix_gameplay_action_audit_user_id", "gameplay_action_audit", ["user_id"])
    op.create_index("ix_gameplay_action_audit_character_id", "gameplay_action_audit", ["character_id"])
    op.create_index("ix_gameplay_action_audit_action_type", "gameplay_action_audit", ["action_type"])


def downgrade() -> None:
    op.drop_index("ix_gameplay_action_audit_action_type", table_name="gameplay_action_audit")
    op.drop_index("ix_gameplay_action_audit_character_id", table_name="gameplay_action_audit")
    op.drop_index("ix_gameplay_action_audit_user_id", table_name="gameplay_action_audit")
    op.drop_index("ix_gameplay_action_audit_session_id", table_name="gameplay_action_audit")
    op.drop_table("gameplay_action_audit")
    op.drop_column("characters", "inventory")
