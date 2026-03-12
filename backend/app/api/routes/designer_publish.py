from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin_context
from app.schemas.designer_publish import (
    DesignerPublishRequest,
    DesignerPublishResponse,
    DesignerWorldPackActivateRequest,
    DesignerWorldPackActivateResponse,
    DesignerWorldPackStageRequest,
    DesignerWorldPackStageResponse,
)
from app.services.admin_audit import write_admin_audit
from app.services.designer_world_promotion import (
    activate_staged_world_pack,
    clear_staged_world_pack,
    stage_world_pack,
)
from app.services.github_publish import (
    GitHubFileChange,
    GitHubPublishError,
    publish_changes_and_dispatch,
)

router = APIRouter(prefix="/designer", tags=["designer"])


@router.post("/publish", response_model=DesignerPublishResponse)
def publish_designer_changes(
    payload: DesignerPublishRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    try:
        result = publish_changes_and_dispatch(
            commit_message=payload.commit_message,
            file_changes=[
                GitHubFileChange(path=entry.path, content=entry.content, encoding=entry.encoding)
                for entry in payload.file_changes
            ],
            trigger_release_workflow=payload.trigger_release_workflow,
            trigger_backend_workflow=payload.trigger_backend_workflow,
            workflow_ref=payload.workflow_ref,
            workflow_inputs=payload.workflow_inputs,
        )
    except GitHubPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "code": "designer_publish_failed"},
        ) from exc

    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="designer_publish",
        target_type="github_repo",
        target_id=result.repo,
        summary=(
            f"branch={result.branch} sha={result.commit_sha} "
            f"release={result.release_workflow_triggered} backend={result.backend_workflow_triggered}"
        ),
    )

    return DesignerPublishResponse(
        repo=result.repo,
        branch=result.branch,
        commit_sha=result.commit_sha,
        release_workflow_triggered=result.release_workflow_triggered,
        backend_workflow_triggered=result.backend_workflow_triggered,
    )


@router.post("/world-pack/stage", response_model=DesignerWorldPackStageResponse)
def stage_designer_world_pack(
    payload: DesignerWorldPackStageRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    try:
        staged = stage_world_pack(payload.pack.model_dump(), actor_user_id=context.user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(exc), "code": "designer_world_pack_invalid"},
        ) from exc

    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="designer_world_stage",
        target_type="world_pack",
        target_id=staged.pack_hash,
        summary=(
            f"province={staged.pack.get('province_id')} "
            f"settlements={len(staged.pack.get('settlements', []))} "
            f"routes={len(staged.pack.get('routes', []))} "
            f"spawns={len(staged.pack.get('spawn_points', []))}"
        ),
    )

    return DesignerWorldPackStageResponse(
        pack_hash=staged.pack_hash,
        settlement_count=len(staged.pack.get("settlements", [])),
        route_count=len(staged.pack.get("routes", [])),
        spawn_count=len(staged.pack.get("spawn_points", [])),
        staged_at=staged.staged_at,
    )


@router.post("/world-pack/activate", response_model=DesignerWorldPackActivateResponse)
def activate_designer_world_pack(
    payload: DesignerWorldPackActivateRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    try:
        promotion = activate_staged_world_pack(payload.expected_pack_hash)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "code": "designer_world_pack_activate_failed"},
        ) from exc

    try:
        publish_result = publish_changes_and_dispatch(
            commit_message=payload.commit_message,
            file_changes=promotion.file_changes,
            trigger_release_workflow=payload.trigger_release_workflow,
            trigger_backend_workflow=payload.trigger_backend_workflow,
            workflow_inputs={"origin": "designer-world-pack", "pack_hash": promotion.pack_hash},
        )
    except GitHubPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "code": "designer_world_pack_publish_failed"},
        ) from exc

    clear_staged_world_pack()

    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="designer_world_activate",
        target_type="world_pack",
        target_id=promotion.pack_hash,
        summary=(
            f"version={promotion.version_key} sha={publish_result.commit_sha} "
            f"release={publish_result.release_workflow_triggered} "
            f"backend={publish_result.backend_workflow_triggered}"
        ),
    )

    return DesignerWorldPackActivateResponse(
        pack_hash=promotion.pack_hash,
        version_key=promotion.version_key,
        repo=publish_result.repo,
        branch=publish_result.branch,
        commit_sha=publish_result.commit_sha,
        release_workflow_triggered=publish_result.release_workflow_triggered,
        backend_workflow_triggered=publish_result.backend_workflow_triggered,
    )
