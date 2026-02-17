"""Add content versioning and bundle tables for data-driven runtime.

Revision ID: 0009_content_model
Revises: 0008_level_layers
Create Date: 2026-02-17 19:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_content_model"
down_revision = "0008_level_layers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("version_key", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("uq_content_versions_key", "content_versions", ["version_key"], unique=True)
    op.create_index("ix_content_versions_state", "content_versions", ["state"], unique=False)

    op.create_table(
        "content_bundles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("content_version_id", sa.Integer(), sa.ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("content_version_id", "domain", name="uq_content_bundles_version_domain"),
    )
    op.create_index("ix_content_bundles_version", "content_bundles", ["content_version_id"], unique=False)
    op.create_index("ix_content_bundles_domain", "content_bundles", ["domain"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_content_bundles_domain", table_name="content_bundles")
    op.drop_index("ix_content_bundles_version", table_name="content_bundles")
    op.drop_table("content_bundles")

    op.drop_index("ix_content_versions_state", table_name="content_versions")
    op.drop_index("uq_content_versions_key", table_name="content_versions")
    op.drop_table("content_versions")
