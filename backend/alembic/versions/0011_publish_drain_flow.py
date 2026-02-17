"""Add publish-drain audit model and draining session fields.

Revision ID: 0011_publish_drain_flow
Revises: 0010_release_registry_gcs
Create Date: 2026-02-18 00:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_publish_drain_flow"
down_revision = "0010_release_registry_gcs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "publish_drain_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("initiated_by", sa.String(length=128), nullable=False),
        sa.Column("content_version_id", sa.Integer(), sa.ForeignKey("content_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_version_key", sa.String(length=64), nullable=False),
        sa.Column("build_version", sa.String(length=64), nullable=True),
        sa.Column("grace_seconds", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cutoff_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draining"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("sessions_targeted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_persisted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_persist_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_revoked", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_publish_drain_events_content_version_id", "publish_drain_events", ["content_version_id"], unique=False)
    op.create_index("ix_publish_drain_events_deadline_at", "publish_drain_events", ["deadline_at"], unique=False)
    op.create_index("ix_publish_drain_events_status", "publish_drain_events", ["status"], unique=False)

    op.create_table(
        "publish_drain_session_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("publish_drain_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persisted_ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("despawned_ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("revoked_ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_publish_drain_session_audit_event_id", "publish_drain_session_audit", ["event_id"], unique=False)
    op.create_index("ix_publish_drain_session_audit_session_id", "publish_drain_session_audit", ["session_id"], unique=False)
    op.create_index("ix_publish_drain_session_audit_user_id", "publish_drain_session_audit", ["user_id"], unique=False)

    op.add_column(
        "user_sessions",
        sa.Column("drain_state", sa.String(length=24), nullable=False, server_default="active"),
    )
    op.add_column(
        "user_sessions",
        sa.Column("drain_event_id", sa.Integer(), sa.ForeignKey("publish_drain_events.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "user_sessions",
        sa.Column("drain_deadline_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_sessions",
        sa.Column("drain_reason_code", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_user_sessions_drain_event_id", "user_sessions", ["drain_event_id"], unique=False)
    op.create_index("ix_user_sessions_drain_state", "user_sessions", ["drain_state"], unique=False)

    op.alter_column("user_sessions", "drain_state", server_default=None)
    op.alter_column("publish_drain_events", "status", server_default=None)
    op.alter_column("publish_drain_events", "notes", server_default=None)
    op.alter_column("publish_drain_events", "sessions_targeted", server_default=None)
    op.alter_column("publish_drain_events", "sessions_persisted", server_default=None)
    op.alter_column("publish_drain_events", "sessions_persist_failed", server_default=None)
    op.alter_column("publish_drain_events", "sessions_revoked", server_default=None)
    op.alter_column("publish_drain_session_audit", "persisted_ok", server_default=None)
    op.alter_column("publish_drain_session_audit", "despawned_ok", server_default=None)
    op.alter_column("publish_drain_session_audit", "revoked_ok", server_default=None)
    op.alter_column("publish_drain_session_audit", "detail", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_user_sessions_drain_state", table_name="user_sessions")
    op.drop_index("ix_user_sessions_drain_event_id", table_name="user_sessions")
    op.drop_column("user_sessions", "drain_reason_code")
    op.drop_column("user_sessions", "drain_deadline_at")
    op.drop_column("user_sessions", "drain_event_id")
    op.drop_column("user_sessions", "drain_state")

    op.drop_index("ix_publish_drain_session_audit_user_id", table_name="publish_drain_session_audit")
    op.drop_index("ix_publish_drain_session_audit_session_id", table_name="publish_drain_session_audit")
    op.drop_index("ix_publish_drain_session_audit_event_id", table_name="publish_drain_session_audit")
    op.drop_table("publish_drain_session_audit")

    op.drop_index("ix_publish_drain_events_status", table_name="publish_drain_events")
    op.drop_index("ix_publish_drain_events_deadline_at", table_name="publish_drain_events")
    op.drop_index("ix_publish_drain_events_content_version_id", table_name="publish_drain_events")
    op.drop_table("publish_drain_events")

