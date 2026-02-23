"""Add party and instance lifecycle tables plus session runtime pointers.

Revision ID: 0019_party_instance_runtime
Revises: 0018_character_appearance_prof
Create Date: 2026-02-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_party_instance_runtime"
down_revision = "0018_character_appearance_prof"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parties",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_parties_owner_user_id", "parties", ["owner_user_id"])
    op.create_index("ix_parties_status", "parties", ["status"])

    op.create_table(
        "party_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("party_id", sa.String(length=64), sa.ForeignKey("parties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("party_id", "user_id", name="uq_party_member_party_user"),
    )
    op.create_index("ix_party_members_party_id", "party_members", ["party_id"])
    op.create_index("ix_party_members_user_id", "party_members", ["user_id"])
    op.create_index("ix_party_members_role", "party_members", ["role"])

    op.create_table(
        "party_invites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("party_id", sa.String(length=64), sa.ForeignKey("parties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inviter_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_party_invites_party_id", "party_invites", ["party_id"])
    op.create_index("ix_party_invites_inviter_user_id", "party_invites", ["inviter_user_id"])
    op.create_index("ix_party_invites_target_user_id", "party_invites", ["target_user_id"])
    op.create_index("ix_party_invites_status", "party_invites", ["status"])

    op.create_table(
        "world_instances",
        sa.Column("id", sa.String(length=96), primary_key=True),
        sa.Column("kind", sa.String(length=16), nullable=False, server_default="solo"),
        sa.Column("level_id", sa.Integer(), sa.ForeignKey("levels.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("party_id", sa.String(length=64), sa.ForeignKey("parties.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_world_instances_kind", "world_instances", ["kind"])
    op.create_index("ix_world_instances_level_id", "world_instances", ["level_id"])
    op.create_index("ix_world_instances_owner_user_id", "world_instances", ["owner_user_id"])
    op.create_index("ix_world_instances_party_id", "world_instances", ["party_id"])
    op.create_index("ix_world_instances_status", "world_instances", ["status"])
    op.create_index("ix_world_instances_expires_at", "world_instances", ["expires_at"])

    op.create_table(
        "world_instance_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("instance_id", sa.String(length=96), sa.ForeignKey("world_instances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("user_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("instance_id", "user_id", name="uq_instance_member_instance_user"),
    )
    op.create_index("ix_world_instance_members_instance_id", "world_instance_members", ["instance_id"])
    op.create_index("ix_world_instance_members_user_id", "world_instance_members", ["user_id"])
    op.create_index("ix_world_instance_members_session_id", "world_instance_members", ["session_id"])
    op.create_index("ix_world_instance_members_character_id", "world_instance_members", ["character_id"])

    op.add_column("levels", sa.Column("is_town_hub", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_levels_is_town_hub", "levels", ["is_town_hub"])
    op.alter_column("levels", "is_town_hub", server_default=None)

    op.add_column(
        "user_sessions",
        sa.Column("current_party_id", sa.String(length=64), sa.ForeignKey("parties.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "user_sessions",
        sa.Column(
            "current_instance_id",
            sa.String(length=96),
            sa.ForeignKey("world_instances.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "user_sessions",
        sa.Column(
            "current_character_id",
            sa.Integer(),
            sa.ForeignKey("characters.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "user_sessions",
        sa.Column("current_level_id", sa.Integer(), sa.ForeignKey("levels.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("user_sessions", sa.Column("current_location_x", sa.Integer(), nullable=True))
    op.add_column("user_sessions", sa.Column("current_location_y", sa.Integer(), nullable=True))
    op.create_index("ix_user_sessions_current_party_id", "user_sessions", ["current_party_id"])
    op.create_index("ix_user_sessions_current_instance_id", "user_sessions", ["current_instance_id"])
    op.create_index("ix_user_sessions_current_character_id", "user_sessions", ["current_character_id"])
    op.create_index("ix_user_sessions_current_level_id", "user_sessions", ["current_level_id"])


def downgrade() -> None:
    op.drop_index("ix_user_sessions_current_level_id", table_name="user_sessions")
    op.drop_index("ix_user_sessions_current_character_id", table_name="user_sessions")
    op.drop_index("ix_user_sessions_current_instance_id", table_name="user_sessions")
    op.drop_index("ix_user_sessions_current_party_id", table_name="user_sessions")
    op.drop_column("user_sessions", "current_location_y")
    op.drop_column("user_sessions", "current_location_x")
    op.drop_column("user_sessions", "current_level_id")
    op.drop_column("user_sessions", "current_character_id")
    op.drop_column("user_sessions", "current_instance_id")
    op.drop_column("user_sessions", "current_party_id")

    op.drop_index("ix_levels_is_town_hub", table_name="levels")
    op.drop_column("levels", "is_town_hub")

    op.drop_index("ix_world_instance_members_character_id", table_name="world_instance_members")
    op.drop_index("ix_world_instance_members_session_id", table_name="world_instance_members")
    op.drop_index("ix_world_instance_members_user_id", table_name="world_instance_members")
    op.drop_index("ix_world_instance_members_instance_id", table_name="world_instance_members")
    op.drop_table("world_instance_members")

    op.drop_index("ix_world_instances_expires_at", table_name="world_instances")
    op.drop_index("ix_world_instances_status", table_name="world_instances")
    op.drop_index("ix_world_instances_party_id", table_name="world_instances")
    op.drop_index("ix_world_instances_owner_user_id", table_name="world_instances")
    op.drop_index("ix_world_instances_level_id", table_name="world_instances")
    op.drop_index("ix_world_instances_kind", table_name="world_instances")
    op.drop_table("world_instances")

    op.drop_index("ix_party_invites_status", table_name="party_invites")
    op.drop_index("ix_party_invites_target_user_id", table_name="party_invites")
    op.drop_index("ix_party_invites_inviter_user_id", table_name="party_invites")
    op.drop_index("ix_party_invites_party_id", table_name="party_invites")
    op.drop_table("party_invites")

    op.drop_index("ix_party_members_role", table_name="party_members")
    op.drop_index("ix_party_members_user_id", table_name="party_members")
    op.drop_index("ix_party_members_party_id", table_name="party_members")
    op.drop_table("party_members")

    op.drop_index("ix_parties_status", table_name="parties")
    op.drop_index("ix_parties_owner_user_id", table_name="parties")
    op.drop_table("parties")
