"""Add GCS release registry and content-version aware policy fields.

Revision ID: 0010_release_registry_gcs
Revises: 0009_content_model
Create Date: 2026-02-17 22:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_release_registry_gcs"
down_revision = "0009_content_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "release_policy",
        sa.Column("latest_content_version_key", sa.String(length=64), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "release_policy",
        sa.Column("min_supported_content_version_key", sa.String(length=64), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "release_policy",
        sa.Column("update_feed_url", sa.Text(), nullable=True),
    )

    op.add_column(
        "user_sessions",
        sa.Column("client_content_version_key", sa.String(length=64), nullable=False, server_default="unknown"),
    )

    op.create_table(
        "release_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("build_version", sa.String(length=64), nullable=False),
        sa.Column("min_supported_version", sa.String(length=64), nullable=False),
        sa.Column("content_version_key", sa.String(length=64), nullable=False),
        sa.Column("min_supported_content_version_key", sa.String(length=64), nullable=False),
        sa.Column("update_feed_url", sa.Text(), nullable=True),
        sa.Column("build_release_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("user_facing_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("activated_by", sa.String(length=128), nullable=False, server_default="system"),
        sa.Column("enforce_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_release_records_activated_at", "release_records", ["activated_at"], unique=False)
    op.create_index("ix_release_records_build_version", "release_records", ["build_version"], unique=False)

    op.execute(
        """
        UPDATE release_policy
        SET
          latest_content_version_key = COALESCE(
            (
              SELECT version_key
              FROM content_versions
              WHERE state = 'active'
              ORDER BY activated_at DESC NULLS LAST, id DESC
              LIMIT 1
            ),
            'cv_bootstrap_v1'
          ),
          min_supported_content_version_key = COALESCE(
            (
              SELECT version_key
              FROM content_versions
              WHERE state = 'active'
              ORDER BY activated_at DESC NULLS LAST, id DESC
              LIMIT 1
            ),
            'cv_bootstrap_v1'
          )
        WHERE id = 1
        """
    )

    op.alter_column("release_policy", "latest_content_version_key", server_default=None)
    op.alter_column("release_policy", "min_supported_content_version_key", server_default=None)
    op.alter_column("user_sessions", "client_content_version_key", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_release_records_build_version", table_name="release_records")
    op.drop_index("ix_release_records_activated_at", table_name="release_records")
    op.drop_table("release_records")

    op.drop_column("user_sessions", "client_content_version_key")

    op.drop_column("release_policy", "update_feed_url")
    op.drop_column("release_policy", "min_supported_content_version_key")
    op.drop_column("release_policy", "latest_content_version_key")
