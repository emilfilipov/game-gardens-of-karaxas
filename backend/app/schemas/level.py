from datetime import datetime

from pydantic import BaseModel, Field


class LevelGridPoint(BaseModel):
    x: int = Field(ge=0, le=100_000)
    y: int = Field(ge=0, le=100_000)


class LevelSummaryResponse(BaseModel):
    id: int
    name: str
    descriptive_name: str
    order_index: int
    schema_version: int
    width: int
    height: int


class LevelLayerCell(BaseModel):
    x: int = Field(ge=0, le=100_000)
    y: int = Field(ge=0, le=100_000)
    asset_key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")


class LevelTransition(BaseModel):
    x: int = Field(ge=0, le=100_000)
    y: int = Field(ge=0, le=100_000)
    transition_type: str = Field(min_length=1, max_length=32, pattern=r"^[a-z_]+$")
    destination_level_id: int = Field(ge=1)


class LevelObjectTransform(BaseModel):
    x: float = Field(ge=0, le=100_000)
    y: float = Field(ge=0, le=100_000)
    z: float = Field(default=0.0, ge=-100_000, le=100_000)
    rotation_deg: float = Field(default=0.0, ge=-360.0, le=360.0)
    scale_x: float = Field(default=1.0, gt=0.0, le=16.0)
    scale_y: float = Field(default=1.0, gt=0.0, le=16.0)
    pivot_x: float = Field(default=0.5, ge=0.0, le=1.0)
    pivot_y: float = Field(default=1.0, ge=0.0, le=1.0)


class LevelObjectPlacement(BaseModel):
    object_id: str = Field(min_length=3, max_length=96, pattern=r"^[a-z0-9_\\-]+$")
    asset_key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    layer_id: int = Field(default=0, ge=0, le=32)
    transform: LevelObjectTransform = Field(default_factory=LevelObjectTransform)


class LevelResponse(BaseModel):
    id: int
    name: str
    descriptive_name: str
    order_index: int
    schema_version: int
    width: int
    height: int
    spawn_x: int
    spawn_y: int
    layers: dict[int, list[LevelLayerCell]]
    objects: list[LevelObjectPlacement]
    transitions: list[LevelTransition]
    wall_cells: list[LevelGridPoint]
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class LevelSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    descriptive_name: str = Field(default="", max_length=96)
    order_index: int | None = Field(default=None, ge=1, le=1_000_000)
    schema_version: int = Field(default=2, ge=1, le=99)
    width: int = Field(default=40, ge=8, le=100_000)
    height: int = Field(default=24, ge=8, le=100_000)
    spawn_x: int = Field(default=1, ge=0, le=100_000)
    spawn_y: int = Field(default=1, ge=0, le=100_000)
    layers: dict[int, list[LevelLayerCell]] = Field(default_factory=dict)
    objects: list[LevelObjectPlacement] = Field(default_factory=list)
    transitions: list[LevelTransition] = Field(default_factory=list)
    wall_cells: list[LevelGridPoint] = Field(default_factory=list)


class LevelOrderItem(BaseModel):
    level_id: int = Field(ge=1)
    order_index: int = Field(ge=1, le=1_000_000)


class LevelOrderSaveRequest(BaseModel):
    levels: list[LevelOrderItem] = Field(default_factory=list)
