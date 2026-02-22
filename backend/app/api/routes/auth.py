from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    AuthContext,
    get_auth_context,
    get_client_content_contract,
    get_client_content_version,
    get_client_version,
    get_db,
)
from app.core.config import settings
from app.core.security import (
    build_totp_qr_svg,
    build_totp_provisioning_uri,
    create_access_token,
    create_refresh_token,
    create_totp_secret,
    hash_password,
    hash_token,
    verify_totp_code,
    verify_password,
)
from app.models.session import UserSession
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MfaSetupResponse,
    MfaStatusResponse,
    MfaToggleRequest,
    RefreshRequest,
    RegisterRequest,
    SessionResponse,
    WsTicketResponse,
)
from app.schemas.common import VersionStatus
from app.services.content import content_contract_signature
from app.services.security_events import write_security_event
from app.services.rate_limit import (
    AUTH_ACCOUNT_RULE,
    AUTH_IP_RULE,
    ensure_not_rate_limited,
    rate_limiter,
    request_ip,
)
from app.services.release_policy import ensure_release_policy, evaluate_version
from app.services.session_drain import enforce_session_drain
from app.services.ws_ticket import issue_ws_ticket

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
        mfa_enabled=user.mfa_enabled,
        expires_at=session.expires_at,
        version_status=_version_status_model(version_status),
    )


def _refresh_ttl_days(user: User) -> int:
    if user.is_admin:
        return max(1, int(settings.jwt_refresh_ttl_days_admin))
    return max(1, int(settings.jwt_refresh_ttl_days))


def _assert_user_mfa(user: User, otp_code: str | None) -> None:
    secret = (user.mfa_totp_secret or "").strip()
    if not user.mfa_enabled:
        return
    if not secret or not verify_totp_code(secret, otp_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid MFA code", "code": "invalid_mfa_code"},
        )


def _revoke_all_user_sessions(
    db: Session,
    *,
    user_id: int,
    reason: str,
    source_session_id: str | None = None,
    ip_address: str | None = None,
) -> int:
    now = datetime.now(UTC)
    sessions = db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
    ).scalars().all()
    for row in sessions:
        row.revoked_at = now
        db.add(row)
    count = len(sessions)
    write_security_event(
        db,
        event_type="session_bulk_revocation",
        severity="critical",
        actor_user_id=user_id,
        session_id=source_session_id,
        ip_address=ip_address,
        detail={"reason": reason, "revoked_sessions": count},
    )
    db.commit()
    return count


@router.post("/register", response_model=SessionResponse)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    client_version: str | None = Depends(get_client_version),
    client_content_version_key: str | None = Depends(get_client_content_version),
    client_content_contract: str | None = Depends(get_client_content_contract),
):
    ip_key = f"ip:{request_ip(request)}"
    ip_addr = request_ip(request)
    account_key = f"acct:{payload.email.lower()}"
    ensure_not_rate_limited("auth_ip", ip_key, AUTH_IP_RULE)
    ensure_not_rate_limited("auth_account", account_key, AUTH_ACCOUNT_RULE)

    exists = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if exists is not None:
        rate_limiter.record_failure("auth_ip", ip_key, AUTH_IP_RULE)
        rate_limiter.record_failure("auth_account", account_key, AUTH_ACCOUNT_RULE)
        write_security_event(
            db,
            event_type="register_conflict",
            severity="warning",
            ip_address=ip_addr,
            detail={"email": payload.email.lower()},
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Email already registered", "code": "email_conflict"},
        )

    normalized_contract = (client_content_contract or "").strip()
    server_contract = content_contract_signature()
    if normalized_contract and normalized_contract != server_contract:
        rate_limiter.record_failure("auth_ip", ip_key, AUTH_IP_RULE)
        rate_limiter.record_failure("auth_account", account_key, AUTH_ACCOUNT_RULE)
        write_security_event(
            db,
            event_type="register_contract_mismatch",
            severity="warning",
            ip_address=ip_addr,
            detail={"email": payload.email.lower()},
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail={
                "message": "Content contract mismatch. Update required before login.",
                "code": "content_contract_mismatch",
                "server_content_contract": server_contract,
                "client_content_contract": normalized_contract,
            },
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
        previous_refresh_token_hash=None,
        client_version=version_status.client_version,
        client_content_version_key=version_status.client_content_version_key,
        refresh_rotated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=_refresh_ttl_days(user)),
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    write_security_event(
        db,
        event_type="register_success",
        severity="info",
        actor_user_id=user.id,
        session_id=session.id,
        ip_address=ip_addr,
        detail={"email": user.email},
    )
    db.commit()
    rate_limiter.reset("auth_ip", ip_key)
    rate_limiter.reset("auth_account", account_key)

    response = _session_response(user, session, version_status)
    response.refresh_token = refresh_token
    return response


@router.post("/login", response_model=SessionResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    client_content_contract: str | None = Depends(get_client_content_contract),
):
    ip_addr = request_ip(request)
    ip_key = f"ip:{ip_addr}"
    account_key = f"acct:{payload.email.lower()}"
    ensure_not_rate_limited("auth_ip", ip_key, AUTH_IP_RULE)
    ensure_not_rate_limited("auth_account", account_key, AUTH_ACCOUNT_RULE)

    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        rate_limiter.record_failure("auth_ip", ip_key, AUTH_IP_RULE)
        rate_limiter.record_failure("auth_account", account_key, AUTH_ACCOUNT_RULE)
        write_security_event(
            db,
            event_type="login_failed_invalid_credentials",
            severity="warning",
            ip_address=ip_addr,
            detail={"email": payload.email.lower()},
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid credentials", "code": "invalid_credentials"},
        )
    try:
        _assert_user_mfa(user, payload.otp_code)
    except HTTPException:
        rate_limiter.record_failure("auth_ip", ip_key, AUTH_IP_RULE)
        rate_limiter.record_failure("auth_account", account_key, AUTH_ACCOUNT_RULE)
        write_security_event(
            db,
            event_type="login_failed_mfa",
            severity="warning",
            actor_user_id=user.id,
            ip_address=ip_addr,
            detail={"email": payload.email.lower()},
            commit=True,
        )
        raise

    release_policy = ensure_release_policy(db)
    version_status = evaluate_version(release_policy, payload.client_version, payload.client_content_version_key)
    normalized_contract = (client_content_contract or "").strip()
    server_contract = content_contract_signature()
    if normalized_contract and normalized_contract != server_contract and not user.is_admin:
        write_security_event(
            db,
            event_type="login_contract_mismatch",
            severity="warning",
            actor_user_id=user.id,
            ip_address=ip_addr,
            detail={"email": payload.email.lower()},
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail={
                "message": "Content contract mismatch. Update required before login.",
                "code": "content_contract_mismatch",
                "server_content_contract": server_contract,
                "client_content_contract": normalized_contract,
            },
        )
    if version_status.force_update and not user.is_admin:
        write_security_event(
            db,
            event_type="login_force_update_block",
            severity="warning",
            actor_user_id=user.id,
            ip_address=ip_addr,
            detail={
                "client_version": payload.client_version,
                "client_content_version_key": payload.client_content_version_key,
            },
            commit=True,
        )
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
        previous_refresh_token_hash=None,
        client_version=payload.client_version,
        client_content_version_key=payload.client_content_version_key,
        refresh_rotated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=_refresh_ttl_days(user)),
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    write_security_event(
        db,
        event_type="login_success",
        severity="info",
        actor_user_id=user.id,
        session_id=session.id,
        ip_address=ip_addr,
        detail={"is_admin": user.is_admin, "mfa_enabled": user.mfa_enabled},
    )
    db.commit()
    rate_limiter.reset("auth_ip", ip_key)
    rate_limiter.reset("auth_account", account_key)

    response = _session_response(user, session, version_status)
    response.refresh_token = refresh_token
    return response


@router.post("/refresh", response_model=SessionResponse)
def refresh(
    payload: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
    client_content_contract: str | None = Depends(get_client_content_contract),
):
    ip_addr = request_ip(request)
    token_hash = hash_token(payload.refresh_token)
    session = db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == token_hash)
    ).scalar_one_or_none()
    if session is None:
        reused_session = db.execute(
            select(UserSession).where(UserSession.previous_refresh_token_hash == token_hash)
        ).scalar_one_or_none()
        if reused_session is not None:
            revoked_count = _revoke_all_user_sessions(
                db,
                user_id=reused_session.user_id,
                reason="refresh_token_reuse_detected",
                source_session_id=reused_session.id,
                ip_address=ip_addr,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Refresh token reuse detected. All sessions revoked.",
                    "code": "refresh_token_reuse_detected",
                    "revoked_sessions": revoked_count,
                },
            )
        write_security_event(
            db,
            event_type="refresh_failed_invalid_token",
            severity="warning",
            ip_address=ip_addr,
            detail={"client_version": payload.client_version},
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid refresh token", "code": "invalid_refresh_token"},
        )

    if session.revoked_at is not None or session.expires_at <= datetime.now(UTC):
        write_security_event(
            db,
            event_type="refresh_failed_expired_session",
            severity="warning",
            actor_user_id=session.user_id,
            session_id=session.id,
            ip_address=ip_addr,
            detail={"client_version": payload.client_version},
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Refresh session expired", "code": "expired_session"},
        )

    user = db.get(User, session.user_id)
    if user is None:
        write_security_event(
            db,
            event_type="refresh_failed_user_not_found",
            severity="warning",
            session_id=session.id,
            ip_address=ip_addr,
            detail="session user missing",
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "User not found", "code": "invalid_session"},
        )

    drain = enforce_session_drain(db, session, user)
    if drain and drain.force_logout:
        write_security_event(
            db,
            event_type="refresh_failed_publish_drain_logout",
            severity="info",
            actor_user_id=user.id,
            session_id=session.id,
            ip_address=ip_addr,
            detail={"event_id": drain.event_id, "reason_code": drain.reason_code},
            commit=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Session invalidated by content publish. Please log in again.",
                "code": "publish_drain_logout",
                "event_id": drain.event_id,
                "reason_code": drain.reason_code,
                "deadline": drain.deadline_at.isoformat() if drain.deadline_at else None,
            },
        )

    release_policy = ensure_release_policy(db)
    version_status = evaluate_version(release_policy, payload.client_version, payload.client_content_version_key)
    normalized_contract = (client_content_contract or "").strip()
    server_contract = content_contract_signature()
    if normalized_contract and normalized_contract != server_contract and not user.is_admin:
        session.revoked_at = datetime.now(UTC)
        db.add(session)
        write_security_event(
            db,
            event_type="refresh_contract_mismatch",
            severity="warning",
            actor_user_id=user.id,
            session_id=session.id,
            ip_address=ip_addr,
            detail={
                "client_content_contract": normalized_contract,
                "server_content_contract": server_contract,
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail={
                "message": "Content contract mismatch. Update required before login.",
                "code": "content_contract_mismatch",
                "server_content_contract": server_contract,
                "client_content_contract": normalized_contract,
            },
        )
    if version_status.force_update and not user.is_admin:
        session.revoked_at = datetime.now(UTC)
        db.add(session)
        write_security_event(
            db,
            event_type="refresh_force_update_block",
            severity="warning",
            actor_user_id=user.id,
            session_id=session.id,
            ip_address=ip_addr,
            detail={
                "client_version": payload.client_version,
                "client_content_version_key": payload.client_content_version_key,
            },
        )
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
    now = datetime.now(UTC)
    session.previous_refresh_token_hash = session.refresh_token_hash
    session.refresh_token_hash = hash_token(new_refresh)
    session.refresh_rotated_at = now
    session.client_version = payload.client_version
    session.client_content_version_key = payload.client_content_version_key
    session.last_seen_at = now
    session.expires_at = now + timedelta(days=_refresh_ttl_days(user))
    db.add(session)
    write_security_event(
        db,
        event_type="refresh_success",
        severity="info",
        actor_user_id=user.id,
        session_id=session.id,
        ip_address=ip_addr,
        detail={"is_admin": user.is_admin},
    )
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
        write_security_event(
            db,
            event_type="logout",
            severity="info",
            actor_user_id=context.user.id,
            session_id=context.session.id,
            detail={"is_admin": context.user.is_admin},
        )
        db.commit()
    return {"ok": True}


@router.post("/ws-ticket", response_model=WsTicketResponse)
def create_ws_ticket(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    ticket, expires_at = issue_ws_ticket(
        db,
        user_id=context.user.id,
        session_id=context.session.id,
    )
    return WsTicketResponse(ws_ticket=ticket, expires_at=expires_at)


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
        "mfa_enabled": context.user.mfa_enabled,
        "mfa_configured": bool((context.user.mfa_totp_secret or "").strip()),
    }


def _load_context_user(context: AuthContext, db: Session) -> User:
    user = db.get(User, context.user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "code": "user_not_found"},
        )
    return user


@router.get("/mfa/status", response_model=MfaStatusResponse)
@router.get("/admin/mfa/status", response_model=MfaStatusResponse, include_in_schema=False)
def mfa_status(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    user = _load_context_user(context, db)
    secret = (user.mfa_totp_secret or "").strip()
    return MfaStatusResponse(
        enabled=user.mfa_enabled,
        configured=bool(secret),
    )


@router.post("/mfa/setup", response_model=MfaSetupResponse)
@router.post("/admin/mfa/setup", response_model=MfaSetupResponse, include_in_schema=False)
def mfa_setup(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    user = _load_context_user(context, db)
    secret = create_totp_secret()
    user.mfa_totp_secret = secret
    db.add(user)
    write_security_event(
        db,
        event_type="mfa_secret_rotated",
        severity="warning",
        actor_user_id=user.id,
        session_id=context.session.id,
        detail={"email": user.email},
    )
    db.commit()
    provisioning_uri = build_totp_provisioning_uri(secret=secret, account_name=user.email)
    return MfaSetupResponse(
        enabled=user.mfa_enabled,
        secret=secret,
        provisioning_uri=provisioning_uri,
        qr_svg=build_totp_qr_svg(provisioning_uri),
    )


@router.get("/mfa/qr", response_model=MfaSetupResponse)
@router.get("/admin/mfa/qr", response_model=MfaSetupResponse, include_in_schema=False)
def mfa_qr(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    user = _load_context_user(context, db)
    secret = (user.mfa_totp_secret or "").strip()
    if not secret:
        secret = create_totp_secret()
        user.mfa_totp_secret = secret
        db.add(user)
        write_security_event(
            db,
            event_type="mfa_secret_generated",
            severity="warning",
            actor_user_id=user.id,
            session_id=context.session.id,
            detail={"email": user.email},
        )
        db.commit()
    provisioning_uri = build_totp_provisioning_uri(secret=secret, account_name=user.email)
    return MfaSetupResponse(
        enabled=user.mfa_enabled,
        secret=secret,
        provisioning_uri=provisioning_uri,
        qr_svg=build_totp_qr_svg(provisioning_uri),
    )


@router.post("/mfa/enable", response_model=MfaStatusResponse)
@router.post("/admin/mfa/enable", response_model=MfaStatusResponse, include_in_schema=False)
def mfa_enable(
    _payload: MfaToggleRequest | None = None,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    user = _load_context_user(context, db)
    secret = (user.mfa_totp_secret or "").strip()
    if not secret:
        secret = create_totp_secret()
        user.mfa_totp_secret = secret
    user.mfa_enabled = True
    user.mfa_enabled_at = datetime.now(UTC)
    db.add(user)
    write_security_event(
        db,
        event_type="mfa_enabled",
        severity="warning",
        actor_user_id=user.id,
        session_id=context.session.id,
        detail={"email": user.email},
    )
    db.commit()
    return MfaStatusResponse(enabled=True, configured=True)


@router.post("/mfa/disable", response_model=MfaStatusResponse)
@router.post("/admin/mfa/disable", response_model=MfaStatusResponse, include_in_schema=False)
def mfa_disable(
    _payload: MfaToggleRequest | None = None,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    user = _load_context_user(context, db)
    secret_was_configured = bool((user.mfa_totp_secret or "").strip())
    user.mfa_enabled = False
    user.mfa_enabled_at = None
    user.mfa_totp_secret = None
    db.add(user)
    write_security_event(
        db,
        event_type="mfa_disabled",
        severity="critical",
        actor_user_id=user.id,
        session_id=context.session.id,
        detail={"email": user.email, "secret_cleared": secret_was_configured},
    )
    db.commit()
    return MfaStatusResponse(enabled=False, configured=False)
