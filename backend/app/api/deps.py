from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import TokenPayloadError, decode_access_token
from app.db.session import SessionLocal
from app.models.release_policy import ReleasePolicy
from app.models.session import UserSession
from app.models.user import User
from app.services.release_policy import ensure_release_policy, evaluate_version

security = HTTPBearer(auto_error=False)


class AuthContext:
    def __init__(self, user: User, session: UserSession, version_status):
        self.user = user
        self.session = session
        self.version_status = version_status


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_client_version(x_client_version: str | None = Header(default=None)) -> str | None:
    return x_client_version


def _unauthorized(message: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": message, "code": "unauthorized"},
    )


def get_auth_context(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    client_version: str | None = Depends(get_client_version),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenPayloadError as exc:
        raise _unauthorized(str(exc)) from exc

    session_id = str(payload["sid"])
    user_id = int(payload["sub"])

    session = db.get(UserSession, session_id)
    if session is None or session.user_id != user_id:
        raise _unauthorized("Session not found")
    if session.revoked_at is not None:
        raise _unauthorized("Session revoked")
    if session.expires_at <= datetime.now(UTC):
        raise _unauthorized("Session expired")

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("User not found")

    policy = ensure_release_policy(db)
    evaluated = evaluate_version(policy, client_version or session.client_version)
    if evaluated.force_update:
        session.revoked_at = datetime.now(UTC)
        db.add(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail={
                "message": "Update required before login",
                "code": "force_update",
                "version_status": {
                    "client_version": evaluated.client_version,
                    "latest_version": evaluated.latest_version,
                    "min_supported_version": evaluated.min_supported_version,
                    "enforce_after": evaluated.enforce_after.isoformat() if evaluated.enforce_after else None,
                    "update_available": evaluated.update_available,
                    "force_update": True,
                },
            },
        )

    session.last_seen_at = datetime.now(UTC)
    if client_version:
        session.client_version = client_version
    db.add(session)
    db.commit()

    return AuthContext(user=user, session=session, version_status=evaluated)


def get_current_user(context: AuthContext = Depends(get_auth_context)) -> User:
    return context.user


def require_admin_context(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not context.user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Admin access required", "code": "admin_required"},
        )
    return context


def get_release_policy(db: Session) -> ReleasePolicy:
    policy = db.execute(select(ReleasePolicy).where(ReleasePolicy.id == 1)).scalar_one_or_none()
    if policy is None:
        policy = ensure_release_policy(db)
    return policy


def require_ops_token(x_ops_token: str | None = Header(default=None)) -> None:
    if not x_ops_token or x_ops_token != settings.ops_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid ops token", "code": "unauthorized"},
        )
