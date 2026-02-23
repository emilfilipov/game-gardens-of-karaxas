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
