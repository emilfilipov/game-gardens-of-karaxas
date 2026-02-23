from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db
from app.models.party import Party, PartyInvite, PartyMember
from app.models.user import User
from app.schemas.party import (
    PartyInviteActionRequest,
    PartyInviteCreateRequest,
    PartyInviteResponse,
    PartyKickRequest,
    PartyMemberResponse,
    PartyPromoteRequest,
    PartyStateResponse,
)
from app.services.party_manager import (
    accept_party_invite,
    create_party_for_owner,
    create_party_invite,
    decline_party_invite,
    ensure_party_owner,
    get_active_party_for_user,
    remove_party_member,
    resolve_invite_target,
    transfer_party_owner,
)

router = APIRouter(prefix="/party", tags=["party"])


def _party_state(db: Session, party: Party) -> PartyStateResponse:
    members = db.execute(select(PartyMember).where(PartyMember.party_id == party.id)).scalars().all()
    users = db.execute(select(User).where(User.id.in_([m.user_id for m in members]))).scalars().all() if members else []
    by_user = {u.id: u for u in users}
    invites = db.execute(
        select(PartyInvite).where(PartyInvite.party_id == party.id, PartyInvite.status == "pending")
    ).scalars().all()
    return PartyStateResponse(
        party_id=party.id,
        owner_user_id=party.owner_user_id,
        status=party.status,
        members=[
            PartyMemberResponse(
                user_id=row.user_id,
                display_name=(by_user.get(row.user_id).display_name if by_user.get(row.user_id) else f"user:{row.user_id}"),
                role=row.role,
                joined_at=row.joined_at,
            )
            for row in members
        ],
        pending_invites=[
            PartyInviteResponse(
                id=invite.id,
                party_id=invite.party_id,
                inviter_user_id=invite.inviter_user_id,
                target_user_id=invite.target_user_id,
                status=invite.status,
                created_at=invite.created_at,
                responded_at=invite.responded_at,
            )
            for invite in invites
        ],
    )


@router.get("/state", response_model=PartyStateResponse | None)
def party_state(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    party = get_active_party_for_user(db, context.user.id)
    if party is None:
        return None
    return _party_state(db, party)


@router.post("/create", response_model=PartyStateResponse)
def create_party(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    party = create_party_for_owner(db, context.user.id)
    db.commit()
    db.refresh(party)
    return _party_state(db, party)


@router.post("/invite", response_model=PartyInviteResponse)
def invite(
    payload: PartyInviteCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    party = create_party_for_owner(db, context.user.id)
    ensure_party_owner(db, party.id, context.user.id)
    target_user = resolve_invite_target(db, payload.target_user_id, payload.target_email)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Invite target not found", "code": "invite_target_not_found"},
        )
    if target_user.id == context.user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Cannot invite yourself", "code": "invalid_invite_target"},
        )
    invite_row = create_party_invite(db, party.id, context.user.id, target_user.id)
    db.commit()
    db.refresh(invite_row)
    return PartyInviteResponse(
        id=invite_row.id,
        party_id=invite_row.party_id,
        inviter_user_id=invite_row.inviter_user_id,
        target_user_id=invite_row.target_user_id,
        status=invite_row.status,
        created_at=invite_row.created_at,
        responded_at=invite_row.responded_at,
    )


@router.post("/invite/accept", response_model=PartyStateResponse)
def invite_accept(
    payload: PartyInviteActionRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    invite_row = db.get(PartyInvite, payload.invite_id)
    if invite_row is None or invite_row.target_user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Invite not found", "code": "invite_not_found"},
        )
    if invite_row.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Invite already handled", "code": "invite_not_pending"},
        )
    try:
        party = accept_party_invite(db, invite_row, context.user.id)
    except ValueError as exc:
        code = str(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Unable to accept invite", "code": code},
        ) from exc
    db.commit()
    db.refresh(party)
    return _party_state(db, party)


@router.post("/invite/decline")
def invite_decline(
    payload: PartyInviteActionRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    invite_row = db.get(PartyInvite, payload.invite_id)
    if invite_row is None or invite_row.target_user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Invite not found", "code": "invite_not_found"},
        )
    if invite_row.status != "pending":
        return {"ok": True, "invite_id": invite_row.id, "status": invite_row.status}
    decline_party_invite(db, invite_row)
    db.commit()
    return {"ok": True, "invite_id": invite_row.id, "status": "declined"}


@router.post("/leave")
def leave_party(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    party = get_active_party_for_user(db, context.user.id)
    if party is None:
        return {"ok": True, "left": False}
    remove_party_member(db, party, context.user.id)
    db.commit()
    return {"ok": True, "left": True}


@router.post("/kick")
def kick_member(
    payload: PartyKickRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    party = get_active_party_for_user(db, context.user.id)
    if party is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Party not found", "code": "party_not_found"},
        )
    try:
        ensure_party_owner(db, party.id, context.user.id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Party owner required", "code": "party_owner_required"},
        ) from exc
    if payload.user_id == context.user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Use leave to leave your own party", "code": "invalid_kick_target"},
        )
    remove_party_member(db, party, payload.user_id)
    db.commit()
    return {"ok": True, "kicked_user_id": payload.user_id}


@router.post("/promote")
def promote_member(
    payload: PartyPromoteRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    party = get_active_party_for_user(db, context.user.id)
    if party is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Party not found", "code": "party_not_found"},
        )
    try:
        ensure_party_owner(db, party.id, context.user.id)
        transfer_party_owner(db, party, payload.user_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Party owner required", "code": "party_owner_required"},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Target user is not a party member", "code": str(exc)},
        ) from exc
    db.commit()
    return {"ok": True, "owner_user_id": payload.user_id}
