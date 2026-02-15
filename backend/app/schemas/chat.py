from datetime import datetime

from pydantic import BaseModel, Field


class ChannelResponse(BaseModel):
    id: int
    name: str
    kind: str
    guild_id: int | None


class ChatMessageCreateRequest(BaseModel):
    channel_id: int
    content: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    id: int
    channel_id: int
    sender_user_id: int
    sender_display_name: str
    content: str
    created_at: datetime


class DirectChannelRequest(BaseModel):
    target_user_id: int
