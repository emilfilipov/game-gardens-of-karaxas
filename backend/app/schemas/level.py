from datetime import datetime

from pydantic import BaseModel, Field


class LevelGridPoint(BaseModel):
    x: int = Field(ge=0, le=1023)
    y: int = Field(ge=0, le=1023)


class LevelSummaryResponse(BaseModel):
    id: int
    name: str
    width: int
    height: int


class LevelResponse(BaseModel):
    id: int
    name: str
    width: int
    height: int
    spawn_x: int
    spawn_y: int
    wall_cells: list[LevelGridPoint]
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class LevelSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    width: int = Field(default=40, ge=8, le=256)
    height: int = Field(default=24, ge=8, le=256)
    spawn_x: int = Field(default=1, ge=0, le=1023)
    spawn_y: int = Field(default=1, ge=0, le=1023)
    wall_cells: list[LevelGridPoint] = Field(default_factory=list)
