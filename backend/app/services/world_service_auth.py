from __future__ import annotations

import hashlib
import hmac
from time import time
from secrets import token_hex

from app.core.config import settings

HEADER_SERVICE_ID = "x-aop-service-id"
HEADER_SCOPE = "x-aop-scope"
HEADER_TIMESTAMP = "x-aop-timestamp"
HEADER_NONCE = "x-aop-nonce"
HEADER_BODY_SHA256 = "x-aop-body-sha256"
HEADER_SIGNATURE = "x-aop-signature"


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_canonical_payload(
    *,
    method: str,
    path_and_query: str,
    service_id: str,
    scope: str,
    timestamp_unix: int,
    nonce: str,
    body_sha256: str,
) -> str:
    return (
        f"{method.upper()}\n"
        f"{path_and_query}\n"
        f"{service_id}\n"
        f"{scope}\n"
        f"{timestamp_unix}\n"
        f"{nonce}\n"
        f"{body_sha256}"
    )


def build_signed_headers(
    *,
    method: str,
    path_and_query: str,
    body: bytes,
    timestamp_unix: int | None = None,
    nonce: str | None = None,
    service_id: str | None = None,
    scope: str | None = None,
    secret: str | None = None,
) -> dict[str, str]:
    resolved_service_id = (service_id or settings.world_service_caller_id).strip()
    resolved_scope = (scope or settings.world_service_scope).strip()
    resolved_secret = secret or settings.world_service_auth_secret
    resolved_timestamp = timestamp_unix if timestamp_unix is not None else int(time())
    resolved_nonce = (nonce or token_hex(16)).strip()

    if not resolved_service_id:
        raise ValueError("world service caller id must not be empty")
    if not resolved_scope:
        raise ValueError("world service scope must not be empty")
    if not resolved_secret:
        raise ValueError("world service auth secret must not be empty")
    if not resolved_nonce:
        raise ValueError("world service nonce must not be empty")

    body_sha256 = _sha256_hex(body)
    canonical = build_canonical_payload(
        method=method,
        path_and_query=path_and_query,
        service_id=resolved_service_id,
        scope=resolved_scope,
        timestamp_unix=resolved_timestamp,
        nonce=resolved_nonce,
        body_sha256=body_sha256,
    )

    signature = hmac.new(
        resolved_secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        HEADER_SERVICE_ID: resolved_service_id,
        HEADER_SCOPE: resolved_scope,
        HEADER_TIMESTAMP: str(resolved_timestamp),
        HEADER_NONCE: resolved_nonce,
        HEADER_BODY_SHA256: body_sha256,
        HEADER_SIGNATURE: signature,
    }


def verify_signature(
    *,
    method: str,
    path_and_query: str,
    body: bytes,
    headers: dict[str, str],
    secret: str,
) -> bool:
    try:
        service_id = headers[HEADER_SERVICE_ID].strip()
        scope = headers[HEADER_SCOPE].strip()
        timestamp_unix = int(headers[HEADER_TIMESTAMP].strip())
        nonce = headers[HEADER_NONCE].strip()
        body_sha256 = headers[HEADER_BODY_SHA256].strip()
        signature = headers[HEADER_SIGNATURE].strip()
    except (KeyError, ValueError):
        return False

    if _sha256_hex(body) != body_sha256:
        return False

    canonical = build_canonical_payload(
        method=method,
        path_and_query=path_and_query,
        service_id=service_id,
        scope=scope,
        timestamp_unix=timestamp_unix,
        nonce=nonce,
        body_sha256=body_sha256,
    )

    expected = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
