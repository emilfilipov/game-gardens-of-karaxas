from pydantic import BaseModel, Field


class ResolveActionRequest(BaseModel):
    character_id: int = Field(ge=1)
    action_nonce: str = Field(min_length=8, max_length=96)
    action_type: str = Field(min_length=1, max_length=32)
    skill_key: str | None = Field(default=None, max_length=64)
    reported_x: int = Field(ge=0, le=1_000_000)
    reported_y: int = Field(ge=0, le=1_000_000)
    delta_seconds: float = Field(default=0.2, gt=0.0, le=5.0)
    enemies_defeated: int = Field(default=0, ge=0, le=100)
    requested_loot_tier: int = Field(default=1, ge=1, le=10)


class ResolveActionResponse(BaseModel):
    accepted: bool
    reason_code: str
    server_damage: float = 0.0
    xp_granted: int = 0
    levels_gained: int = 0
    loot_granted: list[dict] = Field(default_factory=list)
    server_position_x: int
    server_position_y: int
    character_level: int
    character_experience: int


class VerticalSliceLoopRequest(BaseModel):
    character_id: int = Field(ge=1)
    campaign_origin_settlement_id: int = Field(default=101, ge=1)
    campaign_destination_settlement_id: int = Field(default=102, ge=1)
    attacker_army_id: int = Field(default=7001, ge=1)
    defender_army_id: int = Field(default=7002, ge=1)
    attacker_strength: int = Field(default=1200, ge=100, le=50_000)
    defender_strength: int = Field(default=1100, ge=100, le=50_000)
    reward_xp: int = Field(default=60, ge=0, le=5_000)
    tick_now_ms: int = Field(default=2_000, ge=0, le=86_400_000)


class VerticalSliceLoopResponse(BaseModel):
    accepted: bool
    reason_code: str
    battle_instance_id: int
    battle_status: str
    winner_side: str | None = None
    world_commands_queued: int
    campaign_tick: int = 0
    xp_granted: int
    levels_gained: int
    character_level: int
    character_experience: int
    persisted_location_x: int
    persisted_location_y: int


class WorldSyncRequest(BaseModel):
    character_id: int = Field(ge=1)
    last_applied_tick: int = Field(default=0, ge=0)
    include_map: bool = True


class WorldSyncResponse(BaseModel):
    accepted: bool
    reason_code: str
    character_id: int
    server_unix_ms: int
    campaign_tick: int
    tick_interval_ms: int
    stale_after_ms: int
    sync_cursor: str
    world: dict
    warnings: list[str] = Field(default_factory=list)
