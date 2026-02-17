from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.router import api_router
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.chat import ChatChannel
from app.services.content import ensure_content_seed
from app.services.release_policy import ensure_release_policy
from app.services.session_drain import finalize_due_publish_drains

app = FastAPI(title="karaxas-backend", version="0.1.0")
configure_logging()
app.include_router(api_router)


@app.on_event("startup")
def startup_seed() -> None:
    db = SessionLocal()
    try:
        ensure_content_seed(db)
        ensure_release_policy(db)
        finalize_due_publish_drains(db)
        global_channel = db.execute(
            select(ChatChannel).where(ChatChannel.kind == "GLOBAL", ChatChannel.name == "Global")
        ).scalar_one_or_none()
        if global_channel is None:
            db.add(ChatChannel(name="Global", kind="GLOBAL"))
            db.commit()
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation error",
                "code": "validation_error",
                "details": exc.errors(),
                "path": request.url.path,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail), "code": "http_error"}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "code": "internal_error",
                "path": request.url.path,
                "detail": str(exc),
            }
        },
    )
