from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CampaignRegion(Base):
    __tablename__ = "campaign_regions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    region_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    terrain_tag: Mapped[str] = mapped_column(String(32), nullable=False, default="plains", index=True)
    supply_modifier: Mapped[float] = mapped_column(Float(), nullable=False, default=1.0)
    risk_modifier: Mapped[float] = mapped_column(Float(), nullable=False, default=1.0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CampaignFaction(Base):
    __tablename__ = "campaign_factions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    faction_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    culture_tag: Mapped[str] = mapped_column(String(48), nullable=False, default="frankish", index=True)
    treasury: Mapped[int] = mapped_column(nullable=False, default=0)
    legitimacy: Mapped[int] = mapped_column(nullable=False, default=50)
    influence: Mapped[int] = mapped_column(nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CampaignSettlement(Base):
    __tablename__ = "campaign_settlements"
    __table_args__ = (UniqueConstraint("region_id", "name", name="uq_campaign_settlements_region_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    settlement_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("campaign_regions.id", ondelete="CASCADE"), nullable=False, index=True)
    controlling_faction_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_factions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="village", index=True)
    population: Mapped[int] = mapped_column(nullable=False, default=0)
    prosperity: Mapped[int] = mapped_column(nullable=False, default=50)
    defense_level: Mapped[int] = mapped_column(nullable=False, default=1)
    garrison_strength: Mapped[int] = mapped_column(nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CampaignRoute(Base):
    __tablename__ = "campaign_routes"
    __table_args__ = (
        CheckConstraint("origin_settlement_id <> destination_settlement_id", name="ck_campaign_routes_distinct_endpoints"),
        UniqueConstraint("origin_settlement_id", "destination_settlement_id", name="uq_campaign_routes_origin_destination"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    origin_settlement_id: Mapped[int] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destination_settlement_id: Mapped[int] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    travel_hours: Mapped[int] = mapped_column(nullable=False, default=1)
    risk_score: Mapped[int] = mapped_column(nullable=False, default=0)
    is_sea_route: Mapped[bool] = mapped_column(nullable=False, default=False, index=True)
    capacity_tonnage: Mapped[int] = mapped_column(nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CampaignHousehold(Base):
    __tablename__ = "campaign_households"
    __table_args__ = (UniqueConstraint("faction_id", "name", name="uq_campaign_households_faction_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    household_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    faction_id: Mapped[int] = mapped_column(ForeignKey("campaign_factions.id", ondelete="CASCADE"), nullable=False, index=True)
    home_settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    prestige: Mapped[int] = mapped_column(nullable=False, default=0)
    loyalty: Mapped[int] = mapped_column(nullable=False, default=50, index=True)
    wealth: Mapped[int] = mapped_column(nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CampaignArmy(Base):
    __tablename__ = "campaign_armies"
    __table_args__ = (UniqueConstraint("faction_id", "name", name="uq_campaign_armies_faction_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    army_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    faction_id: Mapped[int] = mapped_column(ForeignKey("campaign_factions.id", ondelete="CASCADE"), nullable=False, index=True)
    household_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_households.id", ondelete="SET NULL"), nullable=True, index=True
    )
    current_settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    commander_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    troop_count: Mapped[int] = mapped_column(nullable=False, default=0)
    morale: Mapped[int] = mapped_column(nullable=False, default=50)
    supply_days_remaining: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CampaignCaravan(Base):
    __tablename__ = "campaign_caravans"
    __table_args__ = (
        CheckConstraint(
            "origin_settlement_id IS NULL OR destination_settlement_id IS NULL OR "
            "origin_settlement_id <> destination_settlement_id",
            name="ck_campaign_caravans_distinct_endpoints",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    caravan_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    owner_faction_id: Mapped[int] = mapped_column(ForeignKey("campaign_factions.id", ondelete="CASCADE"), nullable=False, index=True)
    origin_settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    destination_settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    current_settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle", index=True)
    cargo_manifest: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    tonnage: Mapped[int] = mapped_column(nullable=False, default=0)
    departure_tick: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    arrival_tick: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    risk_accumulated: Mapped[int] = mapped_column(nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CampaignEspionageAsset(Base):
    __tablename__ = "campaign_espionage_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    owner_faction_id: Mapped[int] = mapped_column(ForeignKey("campaign_factions.id", ondelete="CASCADE"), nullable=False, index=True)
    target_faction_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_factions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    current_region_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    current_settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_settlements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    codename: Mapped[str] = mapped_column(String(128), nullable=False)
    specialization: Mapped[str] = mapped_column(String(32), nullable=False, default="observer", index=True)
    reliability: Mapped[int] = mapped_column(nullable=False, default=50)
    cover_strength: Mapped[int] = mapped_column(nullable=False, default=50)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="dormant", index=True)
    last_report_tick: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
