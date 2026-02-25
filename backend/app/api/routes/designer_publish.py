from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin_context
from app.schemas.designer_publish import DesignerPublishRequest, DesignerPublishResponse
from app.services.admin_audit import write_admin_audit
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
