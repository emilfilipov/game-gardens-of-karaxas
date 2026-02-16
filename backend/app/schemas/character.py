from datetime import datetime

from pydantic import BaseModel, Field


class CharacterCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    appearance_key: str = Field(default="human_male", min_length=1, max_length=64)
    stat_points_total: int = Field(default=20, ge=1, le=200)
    stats: dict[str, int] = Field(default_factory=dict)
    skills: dict[str, int] = Field(default_factory=dict)


class CharacterResponse(BaseModel):
    id: int
    name: str
    level_id: int | None = None
    location_x: int | None = None
    location_y: int | None = None
    appearance_key: str
    level: int
    experience: int
    experience_to_next_level: int
    stat_points_total: int
    stat_points_used: int
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
