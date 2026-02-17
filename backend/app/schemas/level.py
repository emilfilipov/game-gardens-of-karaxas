from datetime import datetime

from pydantic import BaseModel, Field


class LevelGridPoint(BaseModel):
    x: int = Field(ge=0, le=100_000)
    y: int = Field(ge=0, le=100_000)


class LevelSummaryResponse(BaseModel):
    id: int
    name: str
    schema_version: int
    width: int
    height: int


class LevelLayerCell(BaseModel):
    x: int = Field(ge=0, le=100_000)
    y: int = Field(ge=0, le=100_000)
    asset_key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")


class LevelResponse(BaseModel):
    id: int
    name: str
    schema_version: int
    width: int
    height: int
    spawn_x: int
    spawn_y: int
    layers: dict[int, list[LevelLayerCell]]
    wall_cells: list[LevelGridPoint]
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class LevelSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    schema_version: int = Field(default=2, ge=1, le=99)
    width: int = Field(default=40, ge=8, le=100_000)
    height: int = Field(default=24, ge=8, le=100_000)
    spawn_x: int = Field(default=1, ge=0, le=100_000)
    spawn_y: int = Field(default=1, ge=0, le=100_000)
    layers: dict[int, list[LevelLayerCell]] = Field(default_factory=dict)
    wall_cells: list[LevelGridPoint] = Field(default_factory=list)
