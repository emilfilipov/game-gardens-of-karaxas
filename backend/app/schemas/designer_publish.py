from __future__ import annotations

from pydantic import BaseModel, Field


class DesignerPublishFileChange(BaseModel):
    path: str = Field(min_length=1, max_length=320)
    content: str = Field(default="")
    encoding: str = Field(default="utf-8", pattern="^(utf-8|base64)$")


class DesignerPublishRequest(BaseModel):
    commit_message: str = Field(min_length=3, max_length=220)
    file_changes: list[DesignerPublishFileChange] = Field(min_length=1, max_length=200)
    trigger_release_workflow: bool = True
    trigger_backend_workflow: bool = False
    workflow_ref: str | None = Field(default=None, max_length=80)
    workflow_inputs: dict[str, str] = Field(default_factory=dict)


class DesignerPublishResponse(BaseModel):
    repo: str
    branch: str
    commit_sha: str
    release_workflow_triggered: bool
    backend_workflow_triggered: bool


class WorldSettlementPayload(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=120)
    map_x: int
    map_y: int
    kind: str = Field(min_length=1, max_length=32)


class WorldRoutePayload(BaseModel):
    id: int = Field(gt=0)
    origin: int = Field(gt=0)
    destination: int = Field(gt=0)
    travel_hours: int = Field(gt=0)
    base_risk: int = Field(ge=0)
    is_sea_route: bool = False


class WorldSpawnPointPayload(BaseModel):
    id: int = Field(gt=0)
    key: str = Field(min_length=1, max_length=120)
    settlement_id: int = Field(gt=0)
    spawn_type: str = Field(min_length=1, max_length=32)


class DesignerWorldPackPayload(BaseModel):
    manifest_version: int = 1
    province_id: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=160)
    settlements: list[WorldSettlementPayload] = Field(min_length=1, max_length=2000)
    routes: list[WorldRoutePayload] = Field(min_length=1, max_length=6000)
    spawn_points: list[WorldSpawnPointPayload] = Field(min_length=1, max_length=6000)


class DesignerWorldPackStageRequest(BaseModel):
    pack: DesignerWorldPackPayload


class DesignerWorldPackStageResponse(BaseModel):
    pack_hash: str
    settlement_count: int
    route_count: int
    spawn_count: int
    staged_at: str


class DesignerWorldPackActivateRequest(BaseModel):
    expected_pack_hash: str | None = Field(default=None, min_length=16, max_length=128)
    commit_message: str = Field(min_length=3, max_length=220)
    trigger_release_workflow: bool = True
    trigger_backend_workflow: bool = False


class DesignerWorldPackActivateResponse(BaseModel):
    pack_hash: str
    version_key: str
    repo: str
    branch: str
    commit_sha: str
    release_workflow_triggered: bool
    backend_workflow_triggered: bool


class DesignerWorldPackDeactivateRequest(BaseModel):
    province_id: str = Field(min_length=1, max_length=64)
    commit_message: str = Field(min_length=3, max_length=220)
    trigger_release_workflow: bool = True
    trigger_backend_workflow: bool = False


class DesignerWorldPackDeactivateResponse(BaseModel):
    province_id: str
    deactivated_version_key: str
    repo: str
    branch: str
    commit_sha: str
    release_workflow_triggered: bool
    backend_workflow_triggered: bool


class DesignerWorldPackRollbackRequest(BaseModel):
    province_id: str = Field(min_length=1, max_length=64)
    target_version_key: str | None = Field(default=None, min_length=3, max_length=128)
    commit_message: str = Field(min_length=3, max_length=220)
    trigger_release_workflow: bool = True
    trigger_backend_workflow: bool = False


class DesignerWorldPackRollbackResponse(BaseModel):
    province_id: str
    version_key: str
    pack_hash: str
    repo: str
    branch: str
    commit_sha: str
    release_workflow_triggered: bool
    backend_workflow_triggered: bool
