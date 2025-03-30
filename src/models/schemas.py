from pydantic import BaseModel
from typing import List, Optional

class VideoBase(BaseModel):
    id: str
    title: str
    description: str
    published_at: str
    thumbnail_url: str

class Video(VideoBase):
    channel_title: str
    section: str

    class Config:
        orm_mode = True

class ChannelBase(BaseModel):
    id: str
    section: str

class ChannelCreate(ChannelBase):
    pass

class Channel(ChannelBase):
    title: str
    uploads_playlist_id: str

    class Config:
        orm_mode = True
        