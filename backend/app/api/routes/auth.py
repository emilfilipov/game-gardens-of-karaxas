from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_client_content_version, get_client_version, get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.session import UserSession
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, SessionResponse
from app.schemas.common import VersionStatus
from app.services.release_policy import ensure_release_policy, evaluate_version

router = APIRouter(prefix="/auth", tags=["auth"])


def _version_status_model(version_status) -> VersionStatus:
    return VersionStatus(
        client_version=version_status.client_version,
        latest_version=version_status.latest_version,
        min_supported_version=version_status.min_supported_version,
        client_content_version_key=version_status.client_content_version_key,
        latest_content_version_key=version_status.latest_content_version_key,
        min_supported_content_version_key=version_status.min_supported_content_version_key,
        enforce_after=version_status.enforce_after,
        update_available=version_status.update_available,
        content_update_available=version_status.content_update_available,
        force_update=version_status.force_update,
        update_feed_url=version_status.update_feed_url,
    )


def _version_status_payload(version_status) -> dict:
    return _version_status_model(version_status).model_dump(mode="json")


def _session_response(user: User, session: UserSession, version_status) -> SessionResponse:
    return SessionResponse(
        access_token=create_access_token(user.id, session.id),
        refresh_token="",
        token_type="bearer",
        session_id=session.id,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_admin=user.is_admin,
        expires_at=session.expires_at,
        version_status=_version_status_model(version_status),
    )


@router.post("/register", response_model=SessionResponse)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    client_version: str | None = Depends(get_client_version),
    client_content_version_key: str | None = Depends(get_client_content_version),
):
    exists = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Email already registered", "code": "email_conflict"},
        )

    user = User(
        email=payload.email.lower(),
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    release_policy = ensure_release_policy(db)
    version_status = evaluate_version(release_policy, client_version or "0.0.0", client_content_version_key)
    if version_status.force_update:
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail={
                "message": "Update required before login",
                "code": "force_update",
                "version_status": _version_status_payload(version_status),
            },
        )

    refresh_token = create_refresh_token()
    session = UserSession(
        id=str(uuid4()),
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        client_version=version_status.client_version,
        client_content_version_key=version_status.client_content_version_key,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days),
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    db.commit()

    response = _session_response(user, session, version_status)
    response.refresh_token = refresh_token
    return response


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid credentials", "code": "invalid_credentials"},
        )

    release_policy = ensure_release_policy(db)
    version_status = evaluate_version(release_policy, payload.client_version, payload.client_content_version_key)
    if version_status.force_update and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail={
                "message": "Update required before login",
                "code": "force_update",
                "version_status": _version_status_payload(version_status),
            },
        )

    refresh_token = create_refresh_token()
    session = UserSession(
        id=str(uuid4()),
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        client_version=payload.client_version,
        client_content_version_key=payload.client_content_version_key,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days),
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    db.commit()

    response = _session_response(user, session, version_status)
    response.refresh_token = refresh_token
    return response


@router.post("/refresh", response_model=SessionResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    session = db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == hash_token(payload.refresh_token))
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid refresh token", "code": "invalid_refresh_token"},
        )

    if session.revoked_at is not None or session.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Refresh session expired", "code": "expired_session"},
        )

    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "User not found", "code": "invalid_session"},
        )

    release_policy = ensure_release_policy(db)
    version_status = evaluate_version(release_policy, payload.client_version, payload.client_content_version_key)
    if version_status.force_update and not user.is_admin:
        session.revoked_at = datetime.now(UTC)
        db.add(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail={
                "message": "Update required before login",
                "code": "force_update",
                "version_status": _version_status_payload(version_status),
            },
        )

    new_refresh = create_refresh_token()
    session.refresh_token_hash = hash_token(new_refresh)
    session.client_version = payload.client_version
    session.client_content_version_key = payload.client_content_version_key
    session.last_seen_at = datetime.now(UTC)
    session.expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days)
    db.add(session)
    db.commit()

    response = _session_response(user, session, version_status)
    response.refresh_token = new_refresh
    return response


@router.post("/logout")
def logout(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    session = db.get(UserSession, context.session.id)
    if session is not None:
        session.revoked_at = datetime.now(UTC)
        db.add(session)
        db.commit()
    return {"ok": True}


@router.get("/me")
def me(context: AuthContext = Depends(get_auth_context)):
    return {
        "user_id": context.user.id,
        "email": context.user.email,
        "display_name": context.user.display_name,
        "is_admin": context.user.is_admin,
        "version_status": {
            "client_version": context.version_status.client_version,
            "latest_version": context.version_status.latest_version,
            "min_supported_version": context.version_status.min_supported_version,
            "client_content_version_key": context.version_status.client_content_version_key,
            "latest_content_version_key": context.version_status.latest_content_version_key,
            "min_supported_content_version_key": context.version_status.min_supported_content_version_key,
            "enforce_after": context.version_status.enforce_after,
            "update_available": context.version_status.update_available,
            "content_update_available": context.version_status.content_update_available,
            "force_update": context.version_status.force_update,
            "update_feed_url": context.version_status.update_feed_url,
        },
    }
