"""Add event store, outbox, idempotency, and processor cursor tables.

Revision ID: 0022_event_store_outbox
Revises: 0021_campaign_world_foundation
Create Date: 2026-03-12 11:35:00.000000

Rollback safety notes:
- Tables are dropped in reverse dependency order (`world_processor_cursors` -> `world_command_idempotency` -> `world_outbox` -> `world_events`).
- This migration is additive only; rollback does not touch pre-existing tables.
"""

from alembic import op
import sqlalchemy as sa


revision = "0022_event_store_outbox"
down_revision = "0021_campaign_world_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "world_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("stream_key", sa.String(length=96), nullable=False),
        sa.Column("aggregate_type", sa.String(length=48), nullable=False),
        sa.Column("aggregate_id", sa.String(length=96), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("tick", sa.BigInteger(), nullable=True),
        sa.Column("trace_id", sa.String(length=96), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_world_events_stream_key", "world_events", ["stream_key"])
    op.create_index("ix_world_events_aggregate_type", "world_events", ["aggregate_type"])
    op.create_index("ix_world_events_aggregate_id", "world_events", ["aggregate_id"])
    op.create_index("ix_world_events_event_type", "world_events", ["event_type"])
    op.create_index("ix_world_events_tick", "world_events", ["tick"])
    op.create_index("ix_world_events_trace_id", "world_events", ["trace_id"])
    op.create_index("ix_world_events_idempotency_key", "world_events", ["idempotency_key"])
    op.create_index("ix_world_events_recorded_at", "world_events", ["recorded_at"])

    op.create_table(
        "world_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column("partition_key", sa.String(length=128), nullable=True),
        sa.Column("event_id", sa.BigInteger(), sa.ForeignKey("world_events.id", ondelete="CASCADE"), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("locked_by", sa.String(length=96), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_world_outbox_topic", "world_outbox", ["topic"])
    op.create_index("ix_world_outbox_partition_key", "world_outbox", ["partition_key"])
    op.create_index("ix_world_outbox_event_id", "world_outbox", ["event_id"])
    op.create_index("ix_world_outbox_next_attempt_at", "world_outbox", ["next_attempt_at"])
    op.create_index("ix_world_outbox_locked_by", "world_outbox", ["locked_by"])
    op.create_index("ix_world_outbox_locked_at", "world_outbox", ["locked_at"])
    op.create_index("ix_world_outbox_processed_at", "world_outbox", ["processed_at"])
    op.create_index("ix_world_outbox_unprocessed_topic", "world_outbox", ["topic", "processed_at", "next_attempt_at"])

    op.create_table(
        "world_command_idempotency",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("event_id", sa.BigInteger(), sa.ForeignKey("world_events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("scope", "idempotency_key", name="uq_world_command_idempotency_scope_key"),
    )
    op.create_index("ix_world_command_idempotency_status", "world_command_idempotency", ["status"])
    op.create_index("ix_world_command_idempotency_event_id", "world_command_idempotency", ["event_id"])
    op.create_index("ix_world_command_idempotency_updated_at", "world_command_idempotency", ["updated_at"])

    op.create_table(
        "world_processor_cursors",
        sa.Column("processor_name", sa.String(length=64), primary_key=True),
        sa.Column("last_event_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("world_processor_cursors")

    op.drop_index("ix_world_command_idempotency_updated_at", table_name="world_command_idempotency")
    op.drop_index("ix_world_command_idempotency_event_id", table_name="world_command_idempotency")
    op.drop_index("ix_world_command_idempotency_status", table_name="world_command_idempotency")
    op.drop_table("world_command_idempotency")

    op.drop_index("ix_world_outbox_unprocessed_topic", table_name="world_outbox")
    op.drop_index("ix_world_outbox_processed_at", table_name="world_outbox")
    op.drop_index("ix_world_outbox_locked_at", table_name="world_outbox")
    op.drop_index("ix_world_outbox_locked_by", table_name="world_outbox")
    op.drop_index("ix_world_outbox_next_attempt_at", table_name="world_outbox")
    op.drop_index("ix_world_outbox_event_id", table_name="world_outbox")
    op.drop_index("ix_world_outbox_partition_key", table_name="world_outbox")
    op.drop_index("ix_world_outbox_topic", table_name="world_outbox")
    op.drop_table("world_outbox")

    op.drop_index("ix_world_events_recorded_at", table_name="world_events")
    op.drop_index("ix_world_events_idempotency_key", table_name="world_events")
    op.drop_index("ix_world_events_trace_id", table_name="world_events")
    op.drop_index("ix_world_events_tick", table_name="world_events")
    op.drop_index("ix_world_events_event_type", table_name="world_events")
    op.drop_index("ix_world_events_aggregate_id", table_name="world_events")
    op.drop_index("ix_world_events_aggregate_type", table_name="world_events")
    op.drop_index("ix_world_events_stream_key", table_name="world_events")
    op.drop_table("world_events")
