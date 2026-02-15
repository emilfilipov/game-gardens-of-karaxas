from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db
from app.models.chat import ChatChannel, ChatMember
from app.models.guild import Guild, GuildMember
from app.models.user import Friendship, User
from app.schemas.chat import ChannelResponse
from app.schemas.common import VersionStatus
from app.schemas.lobby import FriendResponse, GuildMemberResponse, GuildResponse, LobbyOverviewResponse

router = APIRouter(prefix="/lobby", tags=["lobby"])


@router.get("/overview", response_model=LobbyOverviewResponse)
def lobby_overview(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    friend_rows = db.execute(
        select(Friendship, User)
        .join(User, User.id == Friendship.friend_user_id)
        .where(and_(Friendship.user_id == context.user.id, Friendship.status == "accepted"))
    ).all()
    friends = [
        FriendResponse(user_id=user.id, display_name=user.display_name, status=friendship.status)
        for friendship, user in friend_rows
    ]

    guild_rows = db.execute(
        select(GuildMember, Guild)
        .join(Guild, Guild.id == GuildMember.guild_id)
        .where(GuildMember.user_id == context.user.id)
    ).all()

    guilds: list[GuildResponse] = []
    for guild_member, guild in guild_rows:
        member_rows = db.execute(
            select(GuildMember, User)
            .join(User, User.id == GuildMember.user_id)
            .where(GuildMember.guild_id == guild.id)
            .order_by(User.display_name.asc())
        ).all()
        members = [
            GuildMemberResponse(user_id=user.id, display_name=user.display_name, rank=member.rank)
            for member, user in member_rows
        ]
        guilds.append(GuildResponse(guild_id=guild.id, guild_name=guild.name, members=members))

    channels_query = (
        select(ChatChannel)
        .outerjoin(ChatMember, ChatMember.channel_id == ChatChannel.id)
        .where((ChatChannel.kind == "GLOBAL") | (ChatMember.user_id == context.user.id))
        .order_by(ChatChannel.kind.asc(), ChatChannel.name.asc())
        .distinct()
    )
    channels = [
        ChannelResponse(id=channel.id, name=channel.name, kind=channel.kind, guild_id=channel.guild_id)
        for channel in db.execute(channels_query).scalars()
    ]

    return LobbyOverviewResponse(
        user_id=context.user.id,
        email=context.user.email,
        display_name=context.user.display_name,
        version_status=VersionStatus(
            client_version=context.version_status.client_version,
            latest_version=context.version_status.latest_version,
            min_supported_version=context.version_status.min_supported_version,
            enforce_after=context.version_status.enforce_after,
            update_available=context.version_status.update_available,
            force_update=context.version_status.force_update,
        ),
        friends=friends,
        guilds=guilds,
        channels=channels,
    )
