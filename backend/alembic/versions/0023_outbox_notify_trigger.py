"""Add PostgreSQL LISTEN/NOTIFY trigger for world_outbox inserts.

Revision ID: 0023_outbox_notify_trigger
Revises: 0022_event_store_outbox
Create Date: 2026-03-12 15:10:00.000000

Rollback safety notes:
- Drops trigger before dropping trigger function.
- This migration only adds PostgreSQL trigger/function objects; no table data is removed.
"""

from alembic import op


revision = "0023_outbox_notify_trigger"
down_revision = "0022_event_store_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION world_outbox_notify_insert() RETURNS trigger AS $$
        DECLARE
            payload_text text;
        BEGIN
            payload_text := json_build_object(
                'outbox_id', NEW.id,
                'topic', NEW.topic,
                'event_id', NEW.event_id
            )::text;
            PERFORM pg_notify('world_outbox_new', payload_text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_world_outbox_notify_insert
        AFTER INSERT ON world_outbox
        FOR EACH ROW
        EXECUTE FUNCTION world_outbox_notify_insert();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_world_outbox_notify_insert ON world_outbox;")
    op.execute("DROP FUNCTION IF EXISTS world_outbox_notify_insert();")
