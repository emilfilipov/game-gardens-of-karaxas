from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import VersionStatus
from app.schemas.level import LevelLayerCell, LevelObjectPlacement, LevelTransition

class CharacterCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    preset_key: str = Field(default="sellsword", min_length=1, max_length=64)
    appearance_key: str = Field(default="human_male", min_length=1, max_length=64)
    appearance_profile: dict = Field(default_factory=dict)
    race: str = Field(default="Human", min_length=1, max_length=64)
    background: str = Field(default="Drifter", min_length=1, max_length=64)
    affiliation: str = Field(default="Unaffiliated", min_length=1, max_length=64)
    stat_points_total: int = Field(default=20, ge=1, le=200)
    equipment: dict[str, str] = Field(default_factory=dict)
    inventory: list[dict] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)
    skills: dict[str, int] = Field(default_factory=dict)


class CharacterResponse(BaseModel):
    id: int
    name: str
    preset_key: str
    level_id: int | None = None
    location_x: int | None = None
    location_y: int | None = None
    appearance_key: str
    appearance_profile: dict
    race: str
    background: str
    affiliation: str
    level: int
    experience: int
    experience_to_next_level: int
    stat_points_total: int
    stat_points_used: int
    equipment: dict[str, str]
    inventory: list[dict]
    stats: dict[str, int]
    skills: dict[str, int]
    is_selected: bool
    created_at: datetime
    updated_at: datetime


class CharacterLevelAssignRequest(BaseModel):
    level_id: int | None = Field(default=None, ge=1)


class CharacterLocationUpdateRequest(BaseModel):
    level_id: int | None = Field(default=None, ge=1)
    location_x: int = Field(ge=0, le=1_000_000)
    location_y: int = Field(ge=0, le=1_000_000)


class CharacterWorldBootstrapRequest(BaseModel):
    override_level_id: int | None = Field(default=None, ge=1)


class CharacterWorldLevelResponse(BaseModel):
    id: int
    name: str
    descriptive_name: str
    width: int
    height: int
    spawn_x: int
    spawn_y: int
    is_town_hub: bool = False
    layers: dict[int, list[LevelLayerCell]] = Field(default_factory=dict)
    objects: list[LevelObjectPlacement] = Field(default_factory=list)
    transitions: list[LevelTransition] = Field(default_factory=list)


class CharacterWorldSpawnResponse(BaseModel):
    tile_x: int
    tile_y: int
    world_x: int
    world_y: int
    source: str


class CharacterWorldRuntimeDescriptor(BaseModel):
    config_key: str
    content_contract_signature: str


class CharacterWorldInstanceResponse(BaseModel):
    id: str
    kind: str
    level_id: int
    party_id: str | None = None
    restored: bool = False
    expires_at: datetime | None = None


class CharacterWorldBootstrapResponse(BaseModel):
    character: CharacterResponse
    level: CharacterWorldLevelResponse
    spawn: CharacterWorldSpawnResponse
    instance: CharacterWorldInstanceResponse
    runtime: CharacterWorldRuntimeDescriptor
    runtime_domains: dict[str, dict] = Field(default_factory=dict)
    player_runtime: dict[str, Any] = Field(default_factory=dict)
    version_status: VersionStatus
