from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PartyInviteCreateRequest(BaseModel):
    target_user_id: int | None = Field(default=None, ge=1)
    target_email: EmailStr | None = None


class PartyKickRequest(BaseModel):
    user_id: int = Field(ge=1)


class PartyPromoteRequest(BaseModel):
    user_id: int = Field(ge=1)


class PartyInviteActionRequest(BaseModel):
    invite_id: int = Field(ge=1)


class PartyMemberResponse(BaseModel):
    user_id: int
    display_name: str
    role: str
    joined_at: datetime


class PartyInviteResponse(BaseModel):
    id: int
    party_id: str
    inviter_user_id: int
    target_user_id: int
    status: str
    created_at: datetime
    responded_at: datetime | None


class PartyStateResponse(BaseModel):
    party_id: str
    owner_user_id: int
    status: str
    members: list[PartyMemberResponse]
    pending_invites: list[PartyInviteResponse]
