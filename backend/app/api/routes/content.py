from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin_context
from app.schemas.content import (
    ContentBootstrapResponse,
    ContentBundleUpsertRequest,
    ContentValidationIssueResponse,
    ContentValidationResponse,
    ContentVersionCreateRequest,
    ContentVersionDetailResponse,
    ContentVersionSummaryResponse,
)
from app.services.content import (
    CONTENT_SCHEMA_VERSION,
    CONTENT_STATE_ACTIVE,
    CONTENT_STATE_RETIRED,
    activate_version,
    create_draft_from_active,
    get_active_snapshot,
    get_content_version_domains,
    get_content_version_or_none,
    list_content_versions,
    upsert_version_bundle,
    validate_version,
)

router = APIRouter(prefix="/content", tags=["content"])


def _to_summary(version) -> ContentVersionSummaryResponse:
    return ContentVersionSummaryResponse(
        id=version.id,
        version_key=version.version_key,
        state=version.state,
        note=version.note or "",
        created_by_user_id=version.created_by_user_id,
        created_at=version.created_at,
        validated_at=version.validated_at,
        activated_at=version.activated_at,
        updated_at=version.updated_at,
    )


def _to_detail(version, domains: dict[str, dict]) -> ContentVersionDetailResponse:
    summary = _to_summary(version)
    return ContentVersionDetailResponse(**summary.model_dump(), domains=domains)


@router.get("/bootstrap", response_model=ContentBootstrapResponse)
def bootstrap_content(db: Session = Depends(get_db)):
    snapshot = get_active_snapshot(db)
    return ContentBootstrapResponse(
        content_schema_version=CONTENT_SCHEMA_VERSION,
        content_version_id=snapshot.content_version_id,
        content_version_key=snapshot.content_version_key,
        fetched_at=snapshot.loaded_at,
        domains=snapshot.domains,
    )


@router.get("/versions", response_model=list[ContentVersionSummaryResponse])
def admin_list_content_versions(context: AuthContext = Depends(require_admin_context), db: Session = Depends(get_db)):
    rows = list_content_versions(db)
    return [_to_summary(row) for row in rows]


@router.get("/versions/{version_id}", response_model=ContentVersionDetailResponse)
def admin_get_content_version(
    version_id: int,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    domains = get_content_version_domains(db, version.id)
    return _to_detail(version, domains)


@router.post("/versions", response_model=ContentVersionDetailResponse)
def admin_create_content_version(
    payload: ContentVersionCreateRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    version = create_draft_from_active(
        db,
        created_by_user_id=context.user.id,
        note=payload.note,
    )
    domains = get_content_version_domains(db, version.id)
    return _to_detail(version, domains)


@router.put("/versions/{version_id}/bundles/{domain}", response_model=ContentValidationResponse)
def admin_upsert_content_bundle(
    version_id: int,
    domain: str,
    payload: ContentBundleUpsertRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    if version.state == CONTENT_STATE_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Active content versions are immutable", "code": "content_active_immutable"},
        )
    if version.state == CONTENT_STATE_RETIRED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Retired content versions are immutable", "code": "content_retired_immutable"},
        )

    issues = upsert_version_bundle(db, version=version, domain=domain.strip(), payload=payload.payload)
    refreshed = get_content_version_or_none(db, version_id)
    return ContentValidationResponse(
        ok=len(issues) == 0,
        issues=[ContentValidationIssueResponse(domain=issue.domain, message=issue.message) for issue in issues],
        state=refreshed.state if refreshed else version.state,
    )


@router.post("/versions/{version_id}/validate", response_model=ContentValidationResponse)
def admin_validate_content_version(
    version_id: int,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    issues = validate_version(db, version)
    refreshed = get_content_version_or_none(db, version_id) or version
    return ContentValidationResponse(
        ok=len(issues) == 0,
        issues=[ContentValidationIssueResponse(domain=issue.domain, message=issue.message) for issue in issues],
        state=refreshed.state,
    )


@router.post("/versions/{version_id}/activate", response_model=ContentValidationResponse)
def admin_activate_content_version(
    version_id: int,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    issues = activate_version(db, version)
    refreshed = get_content_version_or_none(db, version_id) or version
    return ContentValidationResponse(
        ok=len(issues) == 0,
        issues=[ContentValidationIssueResponse(domain=issue.domain, message=issue.message) for issue in issues],
        state=refreshed.state,
    )
