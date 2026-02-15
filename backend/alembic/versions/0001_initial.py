"""Initial karaxas schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-15 09:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "release_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("latest_version", sa.String(length=64), nullable=False, server_default="0.0.0"),
        sa.Column("min_supported_version", sa.String(length=64), nullable=False, server_default="0.0.0"),
        sa.Column("enforce_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=False, server_default="system"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=False),
        sa.Column("client_version", sa.String(length=64), nullable=False, server_default="0.0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"], unique=False)

    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("friend_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="accepted"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "friend_user_id", name="uq_friendship_pair"),
    )

    op.create_table(
        "guilds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("name", name="uq_guild_name"),
    )

    op.create_table(
        "guild_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.Integer(), sa.ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.String(length=32), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("guild_id", "user_id", name="uq_guild_member"),
    )
    op.create_index("ix_guild_members_guild_id", "guild_members", ["guild_id"], unique=False)
    op.create_index("ix_guild_members_user_id", "guild_members", ["user_id"], unique=False)

    op.create_table(
        "chat_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=96), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False, server_default="GLOBAL"),
        sa.Column("guild_id", sa.Integer(), sa.ForeignKey("guilds.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_chat_channels_guild_id", "chat_channels", ["guild_id"], unique=False)

    op.create_table(
        "chat_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("chat_channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("channel_id", "user_id", name="uq_chat_member"),
    )
    op.create_index("ix_chat_members_channel_id", "chat_members", ["channel_id"], unique=False)
    op.create_index("ix_chat_members_user_id", "chat_members", ["user_id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("chat_channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_channel_id", "chat_messages", ["channel_id"], unique=False)
    op.create_index("ix_chat_messages_sender_user_id", "chat_messages", ["sender_user_id"], unique=False)

    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("stat_points_total", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("stat_points_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stats", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_characters_user_id", "characters", ["user_id"], unique=False)

    op.execute(
        """
        INSERT INTO release_policy (id, latest_version, min_supported_version, updated_by)
        VALUES (1, '0.0.0', '0.0.0', 'migration')
        ON CONFLICT (id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO chat_channels (name, kind)
        SELECT 'Global', 'GLOBAL'
        WHERE NOT EXISTS (
          SELECT 1 FROM chat_channels WHERE kind = 'GLOBAL' AND name = 'Global'
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_characters_user_id", table_name="characters")
    op.drop_table("characters")

    op.drop_index("ix_chat_messages_sender_user_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_channel_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_members_user_id", table_name="chat_members")
    op.drop_index("ix_chat_members_channel_id", table_name="chat_members")
    op.drop_table("chat_members")

    op.drop_index("ix_chat_channels_guild_id", table_name="chat_channels")
    op.drop_table("chat_channels")

    op.drop_index("ix_guild_members_user_id", table_name="guild_members")
    op.drop_index("ix_guild_members_guild_id", table_name="guild_members")
    op.drop_table("guild_members")

    op.drop_table("guilds")
    op.drop_table("friendships")

    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_table("release_policy")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
