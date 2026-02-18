"""Add auth security hardening schema (MFA, refresh replay detection, security event audit).

Revision ID: 0014_auth_security_hardening
Revises: 0013_admin_action_audit
Create Date: 2026-02-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0014_auth_security_hardening"
down_revision = "0013_admin_action_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("mfa_totp_secret", sa.String(length=128), nullable=True))
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("users", sa.Column("mfa_enabled_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("user_sessions", sa.Column("previous_refresh_token_hash", sa.String(length=255), nullable=True))
    op.add_column("user_sessions", sa.Column("refresh_rotated_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "security_event_audit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default=sa.text("'info'")),
        sa.Column("ip_address", sa.String(length=96), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_event_audit_actor_user_id", "security_event_audit", ["actor_user_id"], unique=False)
    op.create_index("ix_security_event_audit_session_id", "security_event_audit", ["session_id"], unique=False)
    op.create_index("ix_security_event_audit_event_type", "security_event_audit", ["event_type"], unique=False)
    op.create_index("ix_security_event_audit_created_at", "security_event_audit", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_security_event_audit_created_at", table_name="security_event_audit")
    op.drop_index("ix_security_event_audit_event_type", table_name="security_event_audit")
    op.drop_index("ix_security_event_audit_session_id", table_name="security_event_audit")
    op.drop_index("ix_security_event_audit_actor_user_id", table_name="security_event_audit")
    op.drop_table("security_event_audit")

    op.drop_column("user_sessions", "refresh_rotated_at")
    op.drop_column("user_sessions", "previous_refresh_token_hash")

    op.drop_column("users", "mfa_enabled_at")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_totp_secret")
