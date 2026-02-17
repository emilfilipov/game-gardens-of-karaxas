from __future__ import annotations

from datetime import UTC, datetime
import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.chat import ChatChannel
from app.services.content import ensure_content_seed
from app.services.release_policy import ensure_release_policy
from app.services.session_drain import finalize_due_publish_drains
from app.services.ws_ticket import purge_expired_ws_tickets

app = FastAPI(title="karaxas-backend", version="0.1.0")
configure_logging()
logger = logging.getLogger("karaxas.api")

_cors_origins = [entry.strip() for entry in settings.cors_allowed_origins.split(",") if entry.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
app.include_router(api_router)


@app.on_event("startup")
def startup_seed() -> None:
    db = SessionLocal()
    try:
        ensure_content_seed(db)
        ensure_release_policy(db)
        finalize_due_publish_drains(db)
        purge_expired_ws_tickets(db)
        global_channel = db.execute(
            select(ChatChannel).where(ChatChannel.kind == "GLOBAL", ChatChannel.name == "Global")
        ).scalar_one_or_none()
        if global_channel is None:
            db.add(ChatChannel(name="Global", kind="GLOBAL"))
            db.commit()
    finally:
        db.close()


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return str(request_id)
    return uuid4().hex


def _error_payload(request: Request, *, message: str, code: str, details=None) -> dict:
    payload = {
        "message": message,
        "code": code,
        "path": request.url.path,
        "request_id": _request_id(request),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if details is not None:
        payload["details"] = details
    return {"error": payload}


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", "").strip() or uuid4().hex
    request.state.request_id = request_id

    content_length_raw = request.headers.get("content-length")
    if content_length_raw:
        try:
            if int(content_length_raw) > settings.max_request_body_bytes:
                response = JSONResponse(
                    status_code=413,
                    content=jsonable_encoder(
                        _error_payload(
                            request,
                            message="Request body too large",
                            code="payload_too_large",
                        )
                    ),
                )
                response.headers["X-Request-ID"] = request_id
                return response
        except ValueError:
            pass

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for row in exc.errors():
        details.append(
            {
                "loc": row.get("loc"),
                "msg": row.get("msg"),
                "type": row.get("type"),
            }
        )
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            _error_payload(
                request,
                message="Validation error",
                code="validation_error",
                details=details,
            )
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail), "code": "http_error"}
    message = str(detail.get("message", "Request failed")).strip() or "Request failed"
    code = str(detail.get("code", "http_error")).strip() or "http_error"
    extras = {k: v for k, v in detail.items() if k not in {"message", "code"}}
    payload = _error_payload(request, message=message, code=code, details=extras if extras else None)
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(payload))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error request_id=%s path=%s", _request_id(request), request.url.path)
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(
            _error_payload(
                request,
                message="Internal server error",
                code="internal_error",
            )
        ),
    )
