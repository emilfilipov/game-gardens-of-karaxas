from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.party import Party, PartyInvite, PartyMember
from app.models.user import User


def _party_member_rows(db: Session, party_id: str) -> list[PartyMember]:
    return db.execute(select(PartyMember).where(PartyMember.party_id == party_id)).scalars().all()


def get_active_party_for_user(db: Session, user_id: int) -> Party | None:
    member = db.execute(select(PartyMember).where(PartyMember.user_id == user_id)).scalar_one_or_none()
    if member is None:
        return None
    party = db.get(Party, member.party_id)
    if party is None or party.status != "active":
        return None
    return party


def create_party_for_owner(db: Session, owner_user_id: int) -> Party:
    existing = get_active_party_for_user(db, owner_user_id)
    if existing is not None:
        return existing
    party = Party(id=str(uuid4()), owner_user_id=owner_user_id, status="active")
    db.add(party)
    db.flush()
    db.add(PartyMember(party_id=party.id, user_id=owner_user_id, role="owner"))
    db.flush()
    return party


def ensure_party_owner(db: Session, party_id: str, user_id: int) -> Party:
    party = db.get(Party, party_id)
    if party is None or party.status != "active":
        raise ValueError("party_not_found")
    if party.owner_user_id != user_id:
        raise PermissionError("party_owner_required")
    return party


def resolve_invite_target(db: Session, target_user_id: int | None, target_email: str | None) -> User | None:
    if target_user_id is not None:
        return db.get(User, target_user_id)
    normalized_email = (target_email or "").strip().lower()
    if not normalized_email:
        return None
    return db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()


def create_party_invite(db: Session, party_id: str, inviter_user_id: int, target_user_id: int) -> PartyInvite:
    existing_pending = db.execute(
        select(PartyInvite).where(
            PartyInvite.party_id == party_id,
            PartyInvite.target_user_id == target_user_id,
            PartyInvite.status == "pending",
        )
    ).scalar_one_or_none()
    if existing_pending is not None:
        return existing_pending
    invite = PartyInvite(
        party_id=party_id,
        inviter_user_id=inviter_user_id,
        target_user_id=target_user_id,
        status="pending",
    )
    db.add(invite)
    db.flush()
    return invite


def accept_party_invite(db: Session, invite: PartyInvite, user_id: int) -> Party:
    party = db.get(Party, invite.party_id)
    if party is None or party.status != "active":
        raise ValueError("party_not_found")
    existing_party = get_active_party_for_user(db, user_id)
    if existing_party is not None and existing_party.id != party.id:
        raise ValueError("already_in_party")
    member = db.execute(
        select(PartyMember).where(PartyMember.party_id == party.id, PartyMember.user_id == user_id)
    ).scalar_one_or_none()
    if member is None:
        db.add(PartyMember(party_id=party.id, user_id=user_id, role="member"))
    invite.status = "accepted"
    invite.responded_at = datetime.now(UTC)
    db.add(invite)
    return party


def decline_party_invite(db: Session, invite: PartyInvite) -> None:
    invite.status = "declined"
    invite.responded_at = datetime.now(UTC)
    db.add(invite)


def remove_party_member(db: Session, party: Party, user_id: int) -> None:
    row = db.execute(
        select(PartyMember).where(PartyMember.party_id == party.id, PartyMember.user_id == user_id)
    ).scalar_one_or_none()
    if row is None:
        return
    db.delete(row)
    remaining = _party_member_rows(db, party.id)
    if not remaining:
        party.status = "closed"
        db.add(party)
        return
    if party.owner_user_id == user_id:
        replacement = sorted(remaining, key=lambda r: (r.role != "owner", r.joined_at, r.user_id))[0]
        party.owner_user_id = replacement.user_id
        for member in remaining:
            member.role = "owner" if member.user_id == replacement.user_id else "member"
            db.add(member)
        db.add(party)


def transfer_party_owner(db: Session, party: Party, target_user_id: int) -> None:
    members = _party_member_rows(db, party.id)
    present_ids = {row.user_id for row in members}
    if target_user_id not in present_ids:
        raise ValueError("target_not_in_party")
    party.owner_user_id = target_user_id
    for row in members:
        row.role = "owner" if row.user_id == target_user_id else "member"
        db.add(row)
    db.add(party)
