import os

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.services.world_service_auth import (  # noqa: E402
    HEADER_BODY_SHA256,
    HEADER_SIGNATURE,
    build_signed_headers,
    verify_signature,
)


def test_build_signed_headers_matches_expected_contract_signature() -> None:
    body = b'{"command":"tick"}'
    headers = build_signed_headers(
        method="POST",
        path_and_query="/internal/control/commands",
        body=body,
        timestamp_unix=1_700_000_000,
        nonce="nonce-fixed",
        service_id="fastapi-control-plane",
        scope="world.control.mutate",
        secret="integration-secret",
    )

    assert headers[HEADER_BODY_SHA256] == "5725aa8fab03508932ab9fc291d486b33caf6b2056063b8567b6edb223d33822"
    assert headers[HEADER_SIGNATURE] == "6320082a62cb7ae7e02d4edcc433a6eb390344c1295b5f2b046ecfff2b97808c"

    assert (
        verify_signature(
            method="POST",
            path_and_query="/internal/control/commands",
            body=body,
            headers=headers,
            secret="integration-secret",
        )
        is True
    )


def test_verify_signature_rejects_body_tampering() -> None:
    body = b'{"command":"tick"}'
    headers = build_signed_headers(
        method="POST",
        path_and_query="/internal/control/commands",
        body=body,
        timestamp_unix=1_700_000_000,
        nonce="nonce-tamper",
        service_id="fastapi-control-plane",
        scope="world.control.mutate",
        secret="integration-secret",
    )

    assert (
        verify_signature(
            method="POST",
            path_and_query="/internal/control/commands",
            body=b'{"command":"tick-now"}',
            headers=headers,
            secret="integration-secret",
        )
        is False
    )


def test_build_signed_headers_rejects_empty_scope() -> None:
    with pytest.raises(ValueError):
        build_signed_headers(
            method="POST",
            path_and_query="/internal/control/commands",
            body=b"{}",
            scope=" ",
            secret="integration-secret",
        )
