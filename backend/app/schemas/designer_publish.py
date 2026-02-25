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
