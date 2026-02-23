from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.instance import WorldInstance, WorldInstanceMember
from app.models.session import UserSession
from app.services.observability import record_instance_assignment

INSTANCE_TTL_MINUTES = 90
HUB_INSTANCE_TTL_HOURS = 12


@dataclass
class InstanceAssignment:
    instance_id: str
    instance_kind: str
    level_id: int
    party_id: str | None
    restored: bool
    expires_at: datetime | None


def _solo_instance_id(level_id: int, character_id: int) -> str:
    return f"solo-l{level_id}-c{character_id}"


def _party_instance_id(level_id: int, party_id: str) -> str:
    return f"party-l{level_id}-{party_id}"


def _hub_instance_id(level_id: int) -> str:
    return f"hub-l{level_id}"


def expire_stale_instances(db: Session) -> int:
    now = datetime.now(UTC)
    rows = db.execute(
        select(WorldInstance).where(WorldInstance.status == "active", WorldInstance.expires_at.is_not(None))
    ).scalars().all()
    expired = 0
    for row in rows:
        if row.expires_at is None or row.expires_at > now:
            continue
        row.status = "expired"
        row.last_active_at = now
        db.add(row)
        expired += 1
    if expired:
        db.flush()
    return expired


def _resolve_instance_descriptor(level_id: int, character_id: int, party_id: str | None, is_hub_level: bool) -> tuple[str, str]:
    if is_hub_level:
        return _hub_instance_id(level_id), "hub"
    if party_id:
        return _party_instance_id(level_id, party_id), "party"
    return _solo_instance_id(level_id, character_id), "solo"


def assign_session_world_instance(
    db: Session,
    *,
    session: UserSession,
    user_id: int,
    character_id: int,
    level_id: int,
    party_id: str | None,
    is_hub_level: bool,
) -> InstanceAssignment:
    now = datetime.now(UTC)
    expire_stale_instances(db)

    instance_id, kind = _resolve_instance_descriptor(level_id, character_id, party_id, is_hub_level)
    restored = bool(session.current_instance_id == instance_id)

    instance = db.get(WorldInstance, instance_id)
    ttl = timedelta(hours=HUB_INSTANCE_TTL_HOURS) if kind == "hub" else timedelta(minutes=INSTANCE_TTL_MINUTES)
    expires_at = now + ttl
    if instance is None:
        instance = WorldInstance(
            id=instance_id,
            kind=kind,
            level_id=level_id,
            owner_user_id=user_id,
            party_id=party_id,
            status="active",
            metadata_json={},
            last_active_at=now,
            expires_at=expires_at,
        )
        db.add(instance)
    else:
        instance.status = "active"
        instance.level_id = level_id
        instance.party_id = party_id
        instance.last_active_at = now
        instance.expires_at = expires_at
        db.add(instance)

    membership = db.execute(
        select(WorldInstanceMember).where(WorldInstanceMember.instance_id == instance_id, WorldInstanceMember.user_id == user_id)
    ).scalar_one_or_none()
    if membership is None:
        membership = WorldInstanceMember(
            instance_id=instance_id,
            user_id=user_id,
            session_id=session.id,
            character_id=character_id,
            last_seen_at=now,
        )
    else:
        membership.session_id = session.id
        membership.character_id = character_id
        membership.last_seen_at = now
    db.add(membership)

    session.current_party_id = party_id
    session.current_instance_id = instance_id
    session.current_character_id = character_id
    session.current_level_id = level_id
    db.add(session)
    record_instance_assignment(kind, restored)

    return InstanceAssignment(
        instance_id=instance_id,
        instance_kind=kind,
        level_id=level_id,
        party_id=party_id,
        restored=restored,
        expires_at=expires_at,
    )


def instance_runtime_metrics(db: Session) -> dict:
    active_rows = db.execute(
        select(WorldInstance.kind, func.count(WorldInstance.id))
        .where(WorldInstance.status == "active")
        .group_by(WorldInstance.kind)
    ).all()
    active_by_kind = {str(kind): int(count) for kind, count in active_rows}
    active_total = sum(active_by_kind.values())
    member_total = db.execute(
        select(func.count(WorldInstanceMember.id)).join(
            WorldInstance, WorldInstanceMember.instance_id == WorldInstance.id
        ).where(WorldInstance.status == "active")
    ).scalar_one()
    return {
        "active_instances_total": int(active_total),
        "active_instances_by_kind": active_by_kind,
        "active_instance_members_total": int(member_total or 0),
    }
