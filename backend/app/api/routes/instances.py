from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db
from app.models.instance import WorldInstance, WorldInstanceMember
from app.schemas.instance import InstanceSummaryResponse
from app.services.instance_manager import expire_stale_instances

router = APIRouter(prefix="/instances", tags=["instances"])


@router.get("/current", response_model=InstanceSummaryResponse | None)
def current_instance(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    expire_stale_instances(db)
    instance_id = context.session.current_instance_id
    if not instance_id:
        return None
    row = db.get(WorldInstance, instance_id)
    if row is None:
        return None
    return InstanceSummaryResponse(
        id=row.id,
        kind=row.kind,
        status=row.status,
        level_id=row.level_id,
        party_id=row.party_id,
        last_active_at=row.last_active_at,
        expires_at=row.expires_at,
        restored_from_session=True,
    )


@router.post("/heartbeat")
def heartbeat(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    instance_id = context.session.current_instance_id
    if not instance_id:
        return {"ok": True, "instance_id": None}
    now = datetime.now(UTC)
    instance = db.get(WorldInstance, instance_id)
    if instance is None:
        return {"ok": True, "instance_id": instance_id, "missing": True}
    instance.last_active_at = now
    db.add(instance)
    membership = (
        db.query(WorldInstanceMember)
        .filter(WorldInstanceMember.instance_id == instance_id, WorldInstanceMember.user_id == context.user.id)
        .one_or_none()
    )
    if membership is not None:
        membership.last_seen_at = now
        membership.session_id = context.session.id
        db.add(membership)
    db.commit()
    return {"ok": True, "instance_id": instance_id, "last_active_at": now}
