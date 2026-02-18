from datetime import UTC, datetime, timedelta
import hashlib
import secrets
from uuid import uuid4

from passlib.context import CryptContext
import pyotp
import jwt
from jwt import InvalidTokenError

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayloadError(ValueError):
    pass


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(user_id: int, session_id: str) -> str:
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.jwt_access_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except InvalidTokenError as exc:
        raise TokenPayloadError("Invalid token") from exc
    if "sub" not in payload or "sid" not in payload:
        raise TokenPayloadError("Invalid token payload")
    return payload


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_provisioning_uri(*, secret: str, account_name: str) -> str:
    issuer = (settings.jwt_issuer or "Gardens of Karaxas").strip() or "Gardens of Karaxas"
    return pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)


def verify_totp_code(secret: str, code: str | None) -> bool:
    normalized_secret = (secret or "").strip()
    normalized_code = (code or "").strip().replace(" ", "")
    if not normalized_secret or not normalized_code:
        return False
    return pyotp.TOTP(normalized_secret).verify(normalized_code, valid_window=1)
