"""Create campaign world schema foundation for Rust authority migration.

Revision ID: 0021_campaign_world_foundation
Revises: 0020_gameplay_authority
Create Date: 2026-03-12 11:20:00.000000

Rollback safety notes:
- Drops are executed in reverse dependency order to satisfy foreign-key constraints.
- This migration only adds new tables/indexes; no existing table columns are modified.
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_campaign_world_foundation"
down_revision = "0020_gameplay_authority"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaign_regions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("region_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("terrain_tag", sa.String(length=32), nullable=False, server_default="plains"),
        sa.Column("supply_modifier", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("risk_modifier", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("region_key", name="uq_campaign_regions_region_key"),
    )
    op.create_index("ix_campaign_regions_name", "campaign_regions", ["name"])
    op.create_index("ix_campaign_regions_terrain_tag", "campaign_regions", ["terrain_tag"])

    op.create_table(
        "campaign_factions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("faction_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("culture_tag", sa.String(length=48), nullable=False, server_default="frankish"),
        sa.Column("treasury", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("legitimacy", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("influence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("faction_key", name="uq_campaign_factions_faction_key"),
    )
    op.create_index("ix_campaign_factions_name", "campaign_factions", ["name"])
    op.create_index("ix_campaign_factions_culture_tag", "campaign_factions", ["culture_tag"])

    op.create_table(
        "campaign_settlements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("settlement_key", sa.String(length=64), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("campaign_regions.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "controlling_faction_id",
            sa.Integer(),
            sa.ForeignKey("campaign_factions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="village"),
        sa.Column("population", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prosperity", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("defense_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("garrison_strength", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("settlement_key", name="uq_campaign_settlements_settlement_key"),
        sa.UniqueConstraint("region_id", "name", name="uq_campaign_settlements_region_name"),
    )
    op.create_index("ix_campaign_settlements_region_id", "campaign_settlements", ["region_id"])
    op.create_index("ix_campaign_settlements_controlling_faction_id", "campaign_settlements", ["controlling_faction_id"])
    op.create_index("ix_campaign_settlements_kind", "campaign_settlements", ["kind"])

    op.create_table(
        "campaign_routes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "origin_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "destination_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("travel_hours", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_sea_route", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("capacity_tonnage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("origin_settlement_id <> destination_settlement_id", name="ck_campaign_routes_distinct_endpoints"),
        sa.UniqueConstraint(
            "origin_settlement_id",
            "destination_settlement_id",
            name="uq_campaign_routes_origin_destination",
        ),
    )
    op.create_index("ix_campaign_routes_origin_settlement_id", "campaign_routes", ["origin_settlement_id"])
    op.create_index("ix_campaign_routes_destination_settlement_id", "campaign_routes", ["destination_settlement_id"])
    op.create_index("ix_campaign_routes_is_sea_route", "campaign_routes", ["is_sea_route"])

    op.create_table(
        "campaign_households",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("household_key", sa.String(length=64), nullable=False),
        sa.Column("faction_id", sa.Integer(), sa.ForeignKey("campaign_factions.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "home_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("prestige", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("loyalty", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("wealth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("household_key", name="uq_campaign_households_household_key"),
        sa.UniqueConstraint("faction_id", "name", name="uq_campaign_households_faction_name"),
    )
    op.create_index("ix_campaign_households_faction_id", "campaign_households", ["faction_id"])
    op.create_index("ix_campaign_households_home_settlement_id", "campaign_households", ["home_settlement_id"])
    op.create_index("ix_campaign_households_loyalty", "campaign_households", ["loyalty"])

    op.create_table(
        "campaign_armies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("army_key", sa.String(length=64), nullable=False),
        sa.Column("faction_id", sa.Integer(), sa.ForeignKey("campaign_factions.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "household_id",
            sa.Integer(),
            sa.ForeignKey("campaign_households.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "current_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("commander_name", sa.String(length=128), nullable=True),
        sa.Column("troop_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("morale", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("supply_days_remaining", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("army_key", name="uq_campaign_armies_army_key"),
        sa.UniqueConstraint("faction_id", "name", name="uq_campaign_armies_faction_name"),
    )
    op.create_index("ix_campaign_armies_faction_id", "campaign_armies", ["faction_id"])
    op.create_index("ix_campaign_armies_household_id", "campaign_armies", ["household_id"])
    op.create_index("ix_campaign_armies_current_settlement_id", "campaign_armies", ["current_settlement_id"])
    op.create_index("ix_campaign_armies_status", "campaign_armies", ["status"])

    op.create_table(
        "campaign_caravans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("caravan_key", sa.String(length=64), nullable=False),
        sa.Column(
            "owner_faction_id",
            sa.Integer(),
            sa.ForeignKey("campaign_factions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "origin_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "destination_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "current_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column("cargo_manifest", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("tonnage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("departure_tick", sa.BigInteger(), nullable=True),
        sa.Column("arrival_tick", sa.BigInteger(), nullable=True),
        sa.Column("risk_accumulated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "origin_settlement_id IS NULL OR destination_settlement_id IS NULL OR "
            "origin_settlement_id <> destination_settlement_id",
            name="ck_campaign_caravans_distinct_endpoints",
        ),
        sa.UniqueConstraint("caravan_key", name="uq_campaign_caravans_caravan_key"),
    )
    op.create_index("ix_campaign_caravans_owner_faction_id", "campaign_caravans", ["owner_faction_id"])
    op.create_index("ix_campaign_caravans_origin_settlement_id", "campaign_caravans", ["origin_settlement_id"])
    op.create_index("ix_campaign_caravans_destination_settlement_id", "campaign_caravans", ["destination_settlement_id"])
    op.create_index("ix_campaign_caravans_current_settlement_id", "campaign_caravans", ["current_settlement_id"])
    op.create_index("ix_campaign_caravans_status", "campaign_caravans", ["status"])

    op.create_table(
        "campaign_espionage_assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_key", sa.String(length=64), nullable=False),
        sa.Column(
            "owner_faction_id",
            sa.Integer(),
            sa.ForeignKey("campaign_factions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_faction_id",
            sa.Integer(),
            sa.ForeignKey("campaign_factions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "current_region_id",
            sa.Integer(),
            sa.ForeignKey("campaign_regions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "current_settlement_id",
            sa.Integer(),
            sa.ForeignKey("campaign_settlements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("codename", sa.String(length=128), nullable=False),
        sa.Column("specialization", sa.String(length=32), nullable=False, server_default="observer"),
        sa.Column("reliability", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("cover_strength", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="dormant"),
        sa.Column("last_report_tick", sa.BigInteger(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("asset_key", name="uq_campaign_espionage_assets_asset_key"),
    )
    op.create_index("ix_campaign_espionage_assets_owner_faction_id", "campaign_espionage_assets", ["owner_faction_id"])
    op.create_index("ix_campaign_espionage_assets_target_faction_id", "campaign_espionage_assets", ["target_faction_id"])
    op.create_index("ix_campaign_espionage_assets_current_region_id", "campaign_espionage_assets", ["current_region_id"])
    op.create_index(
        "ix_campaign_espionage_assets_current_settlement_id",
        "campaign_espionage_assets",
        ["current_settlement_id"],
    )
    op.create_index("ix_campaign_espionage_assets_status", "campaign_espionage_assets", ["status"])
    op.create_index("ix_campaign_espionage_assets_specialization", "campaign_espionage_assets", ["specialization"])


def downgrade() -> None:
    op.drop_index("ix_campaign_espionage_assets_specialization", table_name="campaign_espionage_assets")
    op.drop_index("ix_campaign_espionage_assets_status", table_name="campaign_espionage_assets")
    op.drop_index("ix_campaign_espionage_assets_current_settlement_id", table_name="campaign_espionage_assets")
    op.drop_index("ix_campaign_espionage_assets_current_region_id", table_name="campaign_espionage_assets")
    op.drop_index("ix_campaign_espionage_assets_target_faction_id", table_name="campaign_espionage_assets")
    op.drop_index("ix_campaign_espionage_assets_owner_faction_id", table_name="campaign_espionage_assets")
    op.drop_table("campaign_espionage_assets")

    op.drop_index("ix_campaign_caravans_status", table_name="campaign_caravans")
    op.drop_index("ix_campaign_caravans_current_settlement_id", table_name="campaign_caravans")
    op.drop_index("ix_campaign_caravans_destination_settlement_id", table_name="campaign_caravans")
    op.drop_index("ix_campaign_caravans_origin_settlement_id", table_name="campaign_caravans")
    op.drop_index("ix_campaign_caravans_owner_faction_id", table_name="campaign_caravans")
    op.drop_table("campaign_caravans")

    op.drop_index("ix_campaign_armies_status", table_name="campaign_armies")
    op.drop_index("ix_campaign_armies_current_settlement_id", table_name="campaign_armies")
    op.drop_index("ix_campaign_armies_household_id", table_name="campaign_armies")
    op.drop_index("ix_campaign_armies_faction_id", table_name="campaign_armies")
    op.drop_table("campaign_armies")

    op.drop_index("ix_campaign_households_loyalty", table_name="campaign_households")
    op.drop_index("ix_campaign_households_home_settlement_id", table_name="campaign_households")
    op.drop_index("ix_campaign_households_faction_id", table_name="campaign_households")
    op.drop_table("campaign_households")

    op.drop_index("ix_campaign_routes_is_sea_route", table_name="campaign_routes")
    op.drop_index("ix_campaign_routes_destination_settlement_id", table_name="campaign_routes")
    op.drop_index("ix_campaign_routes_origin_settlement_id", table_name="campaign_routes")
    op.drop_table("campaign_routes")

    op.drop_index("ix_campaign_settlements_kind", table_name="campaign_settlements")
    op.drop_index("ix_campaign_settlements_controlling_faction_id", table_name="campaign_settlements")
    op.drop_index("ix_campaign_settlements_region_id", table_name="campaign_settlements")
    op.drop_table("campaign_settlements")

    op.drop_index("ix_campaign_factions_culture_tag", table_name="campaign_factions")
    op.drop_index("ix_campaign_factions_name", table_name="campaign_factions")
    op.drop_table("campaign_factions")

    op.drop_index("ix_campaign_regions_terrain_tag", table_name="campaign_regions")
    op.drop_index("ix_campaign_regions_name", table_name="campaign_regions")
    op.drop_table("campaign_regions")
