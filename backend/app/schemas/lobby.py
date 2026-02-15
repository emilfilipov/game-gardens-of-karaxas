from pydantic import BaseModel

from app.schemas.chat import ChannelResponse
from app.schemas.common import VersionStatus


class FriendResponse(BaseModel):
    user_id: int
    display_name: str
    status: str


class GuildMemberResponse(BaseModel):
    user_id: int
    display_name: str
    rank: str


class GuildResponse(BaseModel):
    guild_id: int
    guild_name: str
    members: list[GuildMemberResponse]


class LobbyOverviewResponse(BaseModel):
    user_id: int
    email: str
    display_name: str
    version_status: VersionStatus
    friends: list[FriendResponse]
    guilds: list[GuildResponse]
    channels: list[ChannelResponse]
